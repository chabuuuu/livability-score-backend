package service

import (
	"context"
	"encoding/base64"
	"fmt"
	"location-service/internal/database"
	"location-service/internal/model"
	"log"
	"os"
	"time"

	firebase "firebase.google.com/go/v4"
	"firebase.google.com/go/v4/messaging"
	"github.com/go-redis/redis/v8"
	"google.golang.org/api/option"
)

const (
	RedisGeoKey     = "properties:high_score"
	NotifyCooldown  = 12 * time.Hour
	SearchRadiusKm  = 20
	RedisFCMKeyPref = "user:fcm:"
)

var FCMClient *messaging.Client

// InitFirebase khởi tạo kết nối đến Firebase bằng Base64 ENV
func InitFirebase() {
	// 1. Lấy chuỗi Base64 từ biến môi trường
	base64Creds := os.Getenv("FIREBASE_CREDENTIALS_BASE64")
	if base64Creds == "" {
		log.Println("⚠️ Biến môi trường FIREBASE_CREDENTIALS_BASE64 chưa được thiết lập.")
		return
	}

	// 2. Decode Base64 sang JSON bytes
	credsBytes, err := base64.StdEncoding.DecodeString(base64Creds)
	if err != nil {
		log.Printf("⚠️ Lỗi decode Base64 Firebase Credentials: %v", err)
		return
	}

	// 3. Sử dụng WithAuthCredentialsJSON để thay thế hàm deprecated.
	// Tham số option.ServiceAccount khẳng định chúng ta đang nạp Service Account.
	opt := option.WithAuthCredentialsJSON(option.ServiceAccount, credsBytes)

	// Khởi tạo App
	app, err := firebase.NewApp(context.Background(), nil, opt)
	if err != nil {
		log.Printf("⚠️ Không thể khởi tạo Firebase App: %v", err)
		return
	}

	client, err := app.Messaging(context.Background())
	if err != nil {
		log.Printf("⚠️ Không thể khởi tạo FCM Client: %v", err)
		return
	}

	FCMClient = client
	log.Println("✅ Firebase Messaging (FCM) đã sẵn sàng (Secure Mode)!")
}

// SaveFCMToken lưu token của user vào Redis (TTL 30 ngày)
func SaveFCMToken(userID, token string) error {
	key := RedisFCMKeyPref + userID
	return database.RedisClient.Set(database.Ctx, key, token, 30*24*time.Hour).Err()
}

// --- PHẦN 1: BACKGROUND WORKER (SYNC) ---
func SyncHighScoresToRedis() {
	log.Println("♻️  Bắt đầu Sync dữ liệu vào Redis...")

	var highScoreProps []model.PropertyLivabilityScore
	err := database.DBScores.Where("score_environment > ? OR score_safety > ?", 8.0, 8.0).Find(&highScoreProps).Error
	if err != nil {
		log.Println("Lỗi query DB Scores:", err)
		return
	}

	if len(highScoreProps) == 0 {
		log.Println("Không tìm thấy BĐS nào đủ điểm cao.")
		return
	}

	var ids []int64
	for _, p := range highScoreProps {
		ids = append(ids, p.PropertyID)
	}

	type GeoResult struct {
		ID  int64
		Lat float64
		Lon float64
	}
	var geoResults []GeoResult

	query := "SELECT id, ST_Y(location::geometry) as lat, ST_X(location::geometry) as lon FROM properties WHERE id IN ?"
	err = database.DBProperties.Raw(query, ids).Scan(&geoResults).Error
	if err != nil {
		log.Println("Lỗi query DB Properties:", err)
		return
	}

	database.RedisClient.Del(database.Ctx, RedisGeoKey)

	var geoLocations []*redis.GeoLocation
	for _, res := range geoResults {
		geoLocations = append(geoLocations, &redis.GeoLocation{
			Name:      fmt.Sprintf("%d", res.ID),
			Latitude:  res.Lat,
			Longitude: res.Lon,
		})
	}

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
func ProcessUserLocation(req model.UserLocationRequest) error {
	locations, err := database.RedisClient.GeoRadius(database.Ctx, RedisGeoKey, req.Longitude, req.Latitude, &redis.GeoRadiusQuery{
		Radius:   SearchRadiusKm,
		Unit:     "km",
		WithDist: true,
		Sort:     "ASC",
	}).Result()

	if err != nil {
		return err
	}

	if len(locations) == 0 {
		return nil
	}

	for _, loc := range locations {
		propertyID := loc.Name
		dist := loc.Dist

		notifyKey := fmt.Sprintf("notify:%s:%s", req.UserID, propertyID)
		exists, _ := database.RedisClient.Exists(database.Ctx, notifyKey).Result()
		if exists > 0 {
			continue
		}

		go sendPushNotification(req.UserID, propertyID, dist)

		database.RedisClient.Set(database.Ctx, notifyKey, "sent", NotifyCooldown)
	}

	return nil
}

func sendPushNotification(userID, propID string, distance float64) {
	log.Printf("Start sending FCM to user %s for property %s", userID, propID)


	if FCMClient == nil {
		log.Println("⚠️ FCM Client chưa được khởi tạo") 
		// Comment log này lại nếu muốn đỡ rác log khi dev không có firebase
		return
	}

	userTokenKey := RedisFCMKeyPref + userID
	fcmToken, err := database.RedisClient.Get(database.Ctx, userTokenKey).Result()

	if err == redis.Nil {
		log.Printf("⚠️ User %s không có FCM Token", userID)
		return
	} else if err != nil {
		log.Printf("❌ Lỗi lấy token từ Redis: %v", err)
		return
	}

	message := &messaging.Message{
		Token: fcmToken,
		Notification: &messaging.Notification{
			Title: "🏠 Phát hiện BĐS đáng sống gần bạn!",
			Body:  fmt.Sprintf("Cách bạn %.0fm có một căn hộ điểm sống cao. Xem ngay!", distance*1000),
		},
		Data: map[string]string{
			"property_id": propID,
			"type":        "NEARBY_ALERT",
		},
		Android: &messaging.AndroidConfig{
			Priority: "high",
			Notification: &messaging.AndroidNotification{
				Sound: "default",
			},
		},
		APNS: &messaging.APNSConfig{
			Payload: &messaging.APNSPayload{
				Aps: &messaging.Aps{
					Sound: "default",
				},
			},
		},
	}

	response, err := FCMClient.Send(context.Background(), message)
	if err != nil {
		log.Printf("❌ Lỗi gửi FCM cho user %s: %v", userID, err)
	} else {
		log.Printf("🚀 [FCM SENT] User: %s | MsgID: %s", userID, response)
	}
}