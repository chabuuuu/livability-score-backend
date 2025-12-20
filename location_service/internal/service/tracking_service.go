package service

import (
	"fmt"
	"location-service/internal/database"
	"location-service/internal/model"
	"log"
	"time"

	"github.com/go-redis/redis/v8"
)

const (
	RedisGeoKey    = "properties:high_score"
	NotifyCooldown = 12 * time.Hour // Không báo lại cùng 1 nhà trong 12 tiếng
    SearchRadiusKm = 0.5            // Bán kính tìm kiếm 500m
)

// --- PHẦN 1: BACKGROUND WORKER (SYNC) ---

// SyncHighScoresToRedis: Quét DB lấy nhà xịn, đẩy vào Redis
func SyncHighScoresToRedis() {
	log.Println("♻️  Bắt đầu Sync dữ liệu vào Redis...")

	// B1: Lấy danh sách PropertyID có điểm cao từ DB Scores
	// Logic ví dụ: Tổng điểm trung bình > 8.0 (hoặc logic phức tạp hơn của bạn)
	var highScoreProps []model.PropertyLivabilityScore
	
    // Query mẫu: lấy các bản ghi có điểm môi trường hoặc an ninh > 8
	err := database.DBScores.Where("score_environment > ? OR score_safety > ?", 8.0, 8.0).Find(&highScoreProps).Error
	if err != nil {
		log.Println("Lỗi query DB Scores:", err)
		return
	}

	if len(highScoreProps) == 0 {
		log.Println("Không tìm thấy BĐS nào đủ điểm cao.")
		return
	}

	// Lấy danh sách ID
	var ids []int64
	for _, p := range highScoreProps {
		ids = append(ids, p.PropertyID)
	}

	// B2: Lấy tọa độ từ DB Properties dựa trên danh sách ID
	// Dùng Raw SQL để trích xuất Lat/Long từ cột PostGIS geometry
	type GeoResult struct {
		ID  int64
		Lat float64
		Lon float64
	}
	var geoResults []GeoResult

	// Cú pháp ST_X, ST_Y của PostGIS
	query := "SELECT id, ST_Y(location::geometry) as lat, ST_X(location::geometry) as lon FROM properties WHERE id IN ?"
	err = database.DBProperties.Raw(query, ids).Scan(&geoResults).Error
	if err != nil {
		log.Println("Lỗi query DB Properties:", err)
		return
	}

	// B3: Đẩy vào Redis Geo
    // Xóa key cũ để làm mới dữ liệu (hoặc dùng strategy update)
    database.RedisClient.Del(database.Ctx, RedisGeoKey)

	var geoLocations []*redis.GeoLocation
	for _, res := range geoResults {
		geoLocations = append(geoLocations, &redis.GeoLocation{
			Name:      fmt.Sprintf("%d", res.ID), // Lưu ID vào Redis
			Latitude:  res.Lat,
			Longitude: res.Lon,
		})
	}

    // Batch add vào Redis
	if len(geoLocations) > 0 {
		_, err = database.RedisClient.GeoAdd(database.Ctx, RedisGeoKey, geoLocations...).Result()
		if err != nil {
			log.Println("Lỗi Redis GeoAdd:", err)
		} else {
			log.Printf("✅ Đã sync thành công %d BĐS điểm cao vào Redis Cache.", len(geoLocations))
		}
	}
}

// --- PHẦN 2: REAL-TIME CHECKING (USER) ---

// ProcessUserLocation: Nhận vị trí user, check Redis, gửi thông báo
func ProcessUserLocation(req model.UserLocationRequest) error {
	// 1. Tìm kiếm trong Redis bán kính 500m
	locations, err := database.RedisClient.GeoRadius(database.Ctx, RedisGeoKey, req.Longitude, req.Latitude, &redis.GeoRadiusQuery{
		Radius:      SearchRadiusKm,
		Unit:        "km",
		WithDist:    true,
		Sort:        "ASC", // Gần nhất trước
	}).Result()

	if err != nil {
		return err
	}

	if len(locations) == 0 {
		return nil // Không có gì gần đây
	}

	// 2. Duyệt qua kết quả tìm thấy
	for _, loc := range locations {
		propertyID := loc.Name
		dist := loc.Dist

		// 3. Check Spam (Rate Limiting)
		// Key: notify:user_123:prop_456
		notifyKey := fmt.Sprintf("notify:%s:%s", req.UserID, propertyID)
		
		exists, _ := database.RedisClient.Exists(database.Ctx, notifyKey).Result()
		if exists > 0 {
			continue // Đã báo rồi, bỏ qua
		}

		// 4. Gửi thông báo (Giả lập)
		go sendPushNotification(req.UserID, propertyID, dist)

		// 5. Set cờ đã báo (hết hạn sau 12h)
		database.RedisClient.Set(database.Ctx, notifyKey, "sent", NotifyCooldown)
	}

	return nil
}

// Hàm giả lập gửi FCM
func sendPushNotification(userID, propID string, distance float64) {
	// Ở đây bạn sẽ gọi tới Firebase Cloud Messaging API
	// Tiêu đề: "Phát hiện khu vực sống tốt!"
	// Nội dung: "BĐS cách bạn 200m có điểm an ninh 9.5/10."
	fmt.Printf("🔔 [PUSH NOTIFICATION] -> User: %s | Property: %s | Distance: %.2f km\n", userID, propID, distance)
}