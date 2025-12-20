package main

import (
	"encoding/json"
	"fmt"
	"location-service/internal/database"
	"location-service/internal/model"
	"location-service/internal/service"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/joho/godotenv"
	"github.com/robfig/cron/v3"
)

// Hàm helper để lấy UserID từ Bearer Token (Logic tương tự Python)
func getUserIDFromToken(c *gin.Context) (string, error) {
	// 1. Lấy header Authorization
	authHeader := c.GetHeader("Authorization")
	if authHeader == "" {
		return "", fmt.Errorf("Authorization header is missing")
	}

	// 2. Kiểm tra format "Bearer <token>"
	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || parts[0] != "Bearer" {
		return "", fmt.Errorf("invalid Authorization header format")
	}
	tokenString := parts[1]

	// 3. Lấy Secret Key
	secretKey := os.Getenv("JWT_SECRET_KEY")
	if secretKey == "" {
		return "", fmt.Errorf("server configuration error: JWT_SECRET_KEY missing")
	}

	// 4. Parse & Validate Token
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		// Validate thuật toán ký (thường là HMAC)
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(secretKey), nil
	})

	if err != nil {
		return "", fmt.Errorf("invalid token: %v", err)
	}

	// 5. Extract Claims
	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		// Logic Python:
		// user_str = payload.get("user")
		// if isinstance(user_str, str): ...
		// elif isinstance(user_str, dict): ...

		userClaim, exists := claims["user"]
		if !exists {
			return "", fmt.Errorf("token payload missing 'user' claim")
		}

		// Case A: 'user' là JSON String (do JWT encode object thành string)
		if userStr, ok := userClaim.(string); ok {
			var userMap map[string]interface{}
			if err := json.Unmarshal([]byte(userStr), &userMap); err != nil {
				return "", fmt.Errorf("failed to parse 'user' claim string")
			}
			return extractUserIDFromMap(userMap)
		}

		// Case B: 'user' là JSON Object (Map)
		if userMap, ok := userClaim.(map[string]interface{}); ok {
			return extractUserIDFromMap(userMap)
		}

		return "", fmt.Errorf("invalid 'user' claim format")
	}

	return "", fmt.Errorf("invalid token claims")
}

// Helper phụ để lấy userId từ map (xử lý kiểu số float64 do JSON unmarshal)
func extractUserIDFromMap(userMap map[string]interface{}) (string, error) {
	val, ok := userMap["userId"]
	if !ok {
		return "", fmt.Errorf("userId not found in user claim")
	}

	// JSON number thường được decode thành float64 trong Go
	if idFloat, ok := val.(float64); ok {
		return fmt.Sprintf("%.0f", idFloat), nil
	}
	// Hoặc string
	if idStr, ok := val.(string); ok {
		return idStr, nil
	}
	
	return "0", nil // Fallback như Python return 0
}

func main() {
	// 0. Load biến môi trường
	err := godotenv.Load()
	if err != nil {
		log.Println("⚠️ Không tìm thấy file .env, sử dụng biến môi trường hệ thống.")
	}

	// 1. Khởi tạo DB
	database.Init()

	// 2. Khởi tạo Background Worker (Cronjob)
	c := cron.New()
	_, err = c.AddFunc("@every 10m", func() {
		service.SyncHighScoresToRedis()
	})
	if err != nil {
		log.Fatal("Lỗi khởi tạo Cron:", err)
	}
	c.Start()
	go service.SyncHighScoresToRedis()

	// 3. Khởi tạo API Server với Gin
	r := gin.Default()

	// Endpoint Ping Vị trí (Yêu cầu Bearer Token)
	r.POST("/api/v1/location/ping", func(c *gin.Context) {
		// Bước 1: Xác thực & Lấy UserID từ Token
		userID, err := getUserIDFromToken(c)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized: " + err.Error()})
			return
		}

		if userID == "0" || userID == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid User ID in token"})
			return
		}

		// Bước 2: Bind dữ liệu vị trí từ JSON body (chỉ còn Latitude, Longitude)
		var req model.UserLocationRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		// Bước 3: Gán UserID lấy từ token vào request struct
		req.UserID = userID

		// Bước 4: Gọi Service xử lý logic
		// (Chạy Goroutine để phản hồi nhanh cho App nếu muốn, nhưng ở đây chạy sync để debug dễ hơn)
		err = service.ProcessUserLocation(req)
		if err != nil {
			// Log lỗi server nhưng không trả 500 cho client để tránh App retry liên tục
			log.Println("Lỗi xử lý vị trí:", err)
		}

		c.JSON(http.StatusOK, gin.H{"status": "success"})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8085"
	}
	log.Printf("Server đang chạy tại cổng %s...", port)
	r.Run(":" + port)
}