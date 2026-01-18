package service

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"location-service/internal/database"
	"location-service/internal/model"
	"log"
	"math"
	"net/http"
	"os"
	"time"

	firebase "firebase.google.com/go/v4"
	"firebase.google.com/go/v4/messaging"
	"github.com/go-redis/redis/v8"
	"google.golang.org/api/option"
)

const (
	// Redis Config
	RedisGeoKey        = "properties:hot_locations" // Key chứa GeoHash của BĐS Hot
	RedisPropDetailKey = "property:detail:"         // Key chứa JSON điểm số + view
	RedisFCMKeyPref    = "user:fcm:"
	RedisUserWeightKey = "user:weights:"

	// Business Config
	MinViewCountToCache = 10             // Chỉ cache BĐS > 50 views
	RecentDaysToCache   = 7              // Hoặc BĐS mới đăng 7 ngày
	NotifyCooldown      = 24 * time.Hour // Cooldown 1 ngày
	SearchRadiusKm      = 5.0            // Quét bán kính 5km
	MinLivabilityScore  = 75.0           // Ngưỡng điểm để báo
	UserServiceURL      = "http://kltn-user-service-be:8080"
)

var FCMClient *messaging.Client

// --- DATA STRUCTURES (Lưu trong Redis & Hứng từ DB) ---

// PropertyAttributes: Dữ liệu chi tiết lưu trong Redis (JSON) để tính toán nhanh
type PropertyAttributes struct {
	ViewCount int                `json:"view_count"`
	Scores    map[string]float64 `json:"scores"`
}

// PropertyRaw: Hứng dữ liệu từ DB Property (PostgreSQL)
type PropertyRaw struct {
	ID        int64
	Lat       float64
	Lon       float64
	ViewCount int
}

// ScoreRaw: Hứng dữ liệu từ DB Scoring (PostgreSQL)
type ScoreRaw struct {
	PropertyID          int64
	ScoreHealthcare     float64
	ScoreEducation      float64
	ScoreShopping       float64
	ScoreTransportation float64
	ScoreEnvironment    float64
	ScoreEntertainment  float64
	ScoreSafety         float64
	FloodImpactScore    float64
	AccidentImpactScore float64
	FutureProjectScore  float64
}

// UserPreferences: Hứng response từ User Service
type UserPreferences struct {
	Healthcare     float64 `json:"preferenceHealthcare"`
	Education      float64 `json:"preferenceEducation"`
	Shopping       float64 `json:"preferenceShopping"`
	Transportation float64 `json:"preferenceTransportation"`
	Environment    float64 `json:"preferenceEnvironment"`
	Entertainment  float64 `json:"preferenceEntertainment"`
	Safety         float64 `json:"preferenceSafety"`
}

// --- INIT FIREBASE & FCM HELPER (GIỮ NGUYÊN CODE CŨ CỦA BẠN) ---
func InitFirebase() {
	base64Creds := os.Getenv("FIREBASE_CREDENTIALS_BASE64")
	if base64Creds == "" {
		log.Println("⚠️ Biến môi trường FIREBASE_CREDENTIALS_BASE64 chưa được thiết lập.")
		return
	}
	credsBytes, err := base64.StdEncoding.DecodeString(base64Creds)
	if err != nil {
		log.Printf("⚠️ Lỗi decode Base64: %v", err)
		return
	}
	opt := option.WithAuthCredentialsJSON(option.ServiceAccount, credsBytes)
	app, err := firebase.NewApp(context.Background(), nil, opt)
	if err != nil {
		log.Printf("⚠️ Lỗi init Firebase App: %v", err)
		return
	}
	client, err := app.Messaging(context.Background())
	if err != nil {
		log.Printf("⚠️ Lỗi init FCM Client: %v", err)
		return
	}
	FCMClient = client
	log.Println("✅ Firebase Messaging (FCM) đã sẵn sàng!")
}

func SaveFCMToken(userID, token string) error {
	key := RedisFCMKeyPref + userID
	return database.RedisClient.Set(database.Ctx, key, token, 30*24*time.Hour).Err()
}

// --- PHẦN 1: BACKGROUND WORKER (APPLICATION-SIDE JOIN) ---
// Thay thế hàm SyncHighScoresToRedis cũ
func SyncHotPropertiesToRedis() {
	log.Println("♻️  [Cron] Bắt đầu Sync BĐS HOT/MỚI vào Redis...")

	// 1. Lấy BĐS Hot/Mới từ DB Property
	var hotProps []PropertyRaw
	sevenDaysAgo := time.Now().AddDate(0, 0, -RecentDaysToCache)

	// Query thô lấy ID, View, Tọa độ
	queryProp := `
		SELECT id, view_count, ST_Y(location::geometry) as lat, ST_X(location::geometry) as lon
		FROM properties 
		WHERE approval_status = 'APPROVED' 
		AND location IS NOT NULL
		AND (view_count >= ? OR created_at >= ?)
	`
	err := database.DBProperties.Raw(queryProp, MinViewCountToCache, sevenDaysAgo).Scan(&hotProps).Error
	if err != nil {
		log.Println("❌ Lỗi query DB Property:", err)
		return
	}

	if len(hotProps) == 0 {
		return
	}

	// 2. Trích xuất ID để query sang DB Scoring
	var propIDs []int64
	for _, p := range hotProps {
		propIDs = append(propIDs, p.ID)
	}

	// 3. Lấy điểm số từ DB Scoring (Cross-DB logic)
	var scores []ScoreRaw
	err = database.DBScores.Table("property_livability_scores").
		Where("property_id IN ?", propIDs).
		Find(&scores).Error
	if err != nil {
		log.Println("❌ Lỗi query DB Scoring:", err)
		return
	}

	// 4. Map dữ liệu Score vào Memory
	scoreMap := make(map[int64]ScoreRaw)
	for _, s := range scores {
		scoreMap[s.PropertyID] = s
	}

	// 5. Đẩy vào Redis (Pipeline)
	pipeline := database.RedisClient.Pipeline()
	// Xóa key Geo cũ để cập nhật mới
	pipeline.Del(database.Ctx, RedisGeoKey)

	syncedCount := 0
	for _, p := range hotProps {
		s, hasScore := scoreMap[p.ID]
		if !hasScore {
			continue // Chỉ cache nếu có điểm
		}

		// 5.1 Add Geo Location
		pipeline.GeoAdd(database.Ctx, RedisGeoKey, &redis.GeoLocation{
			Name:      fmt.Sprintf("%d", p.ID),
			Latitude:  p.Lat,
			Longitude: p.Lon,
		})

		// 5.2 Add Detail Data (JSON) để tính toán nhanh
		attrs := PropertyAttributes{
			ViewCount: p.ViewCount,
			Scores: map[string]float64{
				"score_healthcare":     s.ScoreHealthcare,
				"score_education":      s.ScoreEducation,
				"score_shopping":       s.ScoreShopping,
				"score_transportation": s.ScoreTransportation,
				"score_environment":    s.ScoreEnvironment,
				"score_entertainment":  s.ScoreEntertainment,
				"score_safety":         s.ScoreSafety,
				// Chỉ số đặc biệt
				"flood":    s.FloodImpactScore,
				"accident": s.AccidentImpactScore,
				"project":  s.FutureProjectScore,
			},
		}
		jsonBytes, _ := json.Marshal(attrs)
		// Set TTL 1 giờ (vì worker chạy mỗi 10p, set 1h là an toàn)
		pipeline.Set(database.Ctx, fmt.Sprintf("%s%d", RedisPropDetailKey, p.ID), jsonBytes, 1*time.Hour)
		syncedCount++
	}

	_, err = pipeline.Exec(database.Ctx)
	if err != nil {
		log.Println("❌ Lỗi Pipeline Redis:", err)
	} else {
		log.Printf("✅ Sync hoàn tất: %d BĐS Hot đã vào Cache.", syncedCount)
	}
}

// --- HELPER: LẤY TRỌNG SỐ USER ---
func fetchUserWeights(userID string) (map[string]float64, error) {
	cacheKey := RedisUserWeightKey + userID

	// 1. Thử lấy từ Redis
	cached, err := database.RedisClient.Get(database.Ctx, cacheKey).Result()
	if err == nil {
		var weights map[string]float64
		json.Unmarshal([]byte(cached), &weights)
		return weights, nil
	}

	// Định nghĩa trước trọng số mặc định để dùng khi có lỗi
	defaultWeights := map[string]float64{
		"score_healthcare": 0.15, "score_education": 0.15, "score_shopping": 0.15,
		"score_transportation": 0.15, "score_environment": 0.15, "score_entertainment": 0.15, "score_safety": 0.10,
	}

	// 2. Gọi API User Service
	baseURL := os.Getenv("USER_SERVICE_URL")
	if baseURL == "" {
		baseURL = "http://kltn-user-service-be:8080"
	}

	url := fmt.Sprintf("%s/internal/user/%s", baseURL, userID)

	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(url)
	
	// --- FIX 1: Lỗi mạng/Timeout -> Dùng mặc định ---
	if err != nil {
		log.Printf("⚠️ [UserWeights] Lỗi kết nối User Service: %v. Dùng mặc định.", err)
		return defaultWeights, nil 
	}
	defer resp.Body.Close()

	// --- FIX 2: Status Code lỗi -> Dùng mặc định ---
	if resp.StatusCode != 200 {
		log.Printf("⚠️ [UserWeights] User Service trả về %d. Dùng mặc định.", resp.StatusCode)
		return defaultWeights, nil
	}

	var apiResp struct {
		Data UserPreferences `json:"data"`
	}
	body, _ := ioutil.ReadAll(resp.Body) // Hoặc io.ReadAll với Go mới
	if err := json.Unmarshal(body, &apiResp); err != nil {
		log.Printf("⚠️ [UserWeights] Lỗi parse JSON: %v. Dùng mặc định.", err)
		return defaultWeights, nil
	}

	// 3. Normalize
	p := apiResp.Data
	total := p.Healthcare + p.Education + p.Shopping + p.Transportation + p.Environment + p.Entertainment + p.Safety

	// Nếu user chưa set gì (tổng = 0) -> Dùng mặc định
	if total == 0 {
		return defaultWeights, nil
	}

	// Tính toán trọng số chuẩn hóa
	weights := map[string]float64{
		"score_healthcare":     p.Healthcare / total,
		"score_education":      p.Education / total,
		"score_shopping":       p.Shopping / total,
		"score_transportation": p.Transportation / total,
		"score_environment":    p.Environment / total,
		"score_entertainment":  p.Entertainment / total,
		"score_safety":         p.Safety / total,
	}

	// Cache 10 phút nếu lấy thành công
	wBytes, _ := json.Marshal(weights)
	database.RedisClient.Set(database.Ctx, cacheKey, wBytes, 10*time.Minute)

	return weights, nil
}

// --- PHẦN 2: REAL-TIME CHECKING (LOGIC MỚI) ---
func ProcessUserLocation(req model.UserLocationRequest) error {
	// 1. Tìm BĐS Hot trong bán kính 5km
	locations, err := database.RedisClient.GeoRadius(database.Ctx, RedisGeoKey, req.Longitude, req.Latitude, &redis.GeoRadiusQuery{
		Radius:   SearchRadiusKm,
		Unit:     "km",
		WithDist: true,
		Sort:     "ASC",
		Count:    10, // Max 10 căn gần nhất
	}).Result()

	if err != nil || len(locations) == 0 {
		return nil
	}

	// 2. Lấy trọng số User
	userWeights, err := fetchUserWeights(req.UserID)
	if err != nil {
		log.Printf("⚠️ Lỗi lấy weight user %s: %v", req.UserID, err)
		return nil // Fail safe, không làm gì cả
	}

	for _, loc := range locations {
		propID := loc.Name
		dist := loc.Dist

		// Check Cooldown
		notifyKey := fmt.Sprintf("notify:%s:%s", req.UserID, propID)
		exists, _ := database.RedisClient.Exists(database.Ctx, notifyKey).Result()
		if exists > 0 {
			continue
		}

		// 3. Lấy Detail từ Redis
		jsonStr, err := database.RedisClient.Get(database.Ctx, RedisPropDetailKey+propID).Result()
		if err != nil {
			continue
		}
		var attrs PropertyAttributes
		json.Unmarshal([]byte(jsonStr), &attrs)

		// 4. TÍNH ĐIỂM LIVABILITY (Công thức chuẩn)
		// Lấy giá trị thô
		scores := attrs.Scores
		sTrans := scores["score_transportation"]
		sEnv := scores["score_environment"]
		sSafety := scores["score_safety"]
		
		pFlood := scores["flood"]
		pAccident := scores["accident"]
		pProject := scores["project"]

		// Áp dụng Phạt (Penalty)
		sTrans = math.Max(0, sTrans - (2.0*pFlood + 0.5*pAccident))
		sEnv = math.Max(0, sEnv - (1.0*pFlood))
		sSafety = math.Max(0, sSafety - (1.5*pAccident))

		// Map điểm đã phạt
		calcMap := map[string]float64{
			"score_healthcare":     scores["score_healthcare"],
			"score_education":      scores["score_education"],
			"score_shopping":       scores["score_shopping"],
			"score_transportation": sTrans,
			"score_environment":    sEnv,
			"score_entertainment":  scores["score_entertainment"],
			"score_safety":         sSafety,
		}

		// Weighted Sum
		var personalizedScore float64
		for key, w := range userWeights {
			if val, ok := calcMap[key]; ok {
				personalizedScore += val * w
			}
		}

		// Bonus Project
		personalizedScore += pProject * 1.0
		
		// Cap [0-100]
		if personalizedScore > 100 { personalizedScore = 100 }

		// 5. Kiểm tra điều kiện gửi Noti
		// Phải > 75 điểm (Hợp gu)
		if personalizedScore >= MinLivabilityScore {
			go sendPushNotification(req.UserID, propID, dist, personalizedScore, attrs.ViewCount)
			
			// Set Cooldown
			database.RedisClient.Set(database.Ctx, notifyKey, "sent", NotifyCooldown)
		}
	}

	return nil
}

func sendPushNotification(userID, propID string, distance, score float64, views int) {
	if FCMClient == nil { return }

	userTokenKey := RedisFCMKeyPref + userID
	fcmToken, err := database.RedisClient.Get(database.Ctx, userTokenKey).Result()
	if err != nil { return }

	message := &messaging.Message{
		Token: fcmToken,
		Notification: &messaging.Notification{
			Title: "🔔 BĐS phù hợp lối sống của bạn!",
			Body:  fmt.Sprintf("Cách %.1fkm | Điểm hợp gu: %.0f/100 | 🔥 %d người xem", distance, score, views),
		},
		Data: map[string]string{
			"property_id": propID,
			"type":        "SMART_ALERT",
			"score":       fmt.Sprintf("%.2f", score),
		},
		Android: &messaging.AndroidConfig{
			Priority: "high",
			Notification: &messaging.AndroidNotification{Sound: "default"},
		},
		APNS: &messaging.APNSConfig{
			Payload: &messaging.APNSPayload{Aps: &messaging.Aps{Sound: "default"}},
		},
	}

	FCMClient.Send(context.Background(), message)
	log.Printf("🚀 Noti sent to User %s | Prop %s | Score %.1f", userID, propID, score)
}