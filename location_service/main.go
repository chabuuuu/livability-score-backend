package main

import (
	"location-service/internal/database"
	"location-service/internal/model"
	"location-service/internal/service"
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/robfig/cron/v3"
)

func main() {
	// 0. Load biến môi trường từ file .env
	// Cần chạy: go get github.com/joho/godotenv
	err := godotenv.Load()
	if err != nil {
		log.Println("⚠️ Không tìm thấy file .env, sử dụng biến môi trường hệ thống.")
	} else {
		log.Println("✅ Đã load cấu hình từ .env")
	}

	// 1. Khởi tạo DB
	database.Init()

	// 2. Khởi tạo Background Worker (Cronjob)
	c := cron.New()
	// Chạy sync mỗi 10 phút một lần: "*/10 * * * *"
	_, err = c.AddFunc("@every 10m", func() {
		service.SyncHighScoresToRedis()
	})
	if err != nil {
		log.Fatal("Lỗi khởi tạo Cron:", err)
	}
	c.Start()

	// Chạy sync lần đầu tiên ngay lập tức khi start app
	go service.SyncHighScoresToRedis()

	// 3. Khởi tạo API Server với Gin
	r := gin.Default()

	// Endpoint để Mobile App ping vị trí
	r.POST("/api/v1/location/ping", func(c *gin.Context) {
		var req model.UserLocationRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		// Gọi service xử lý
		err := service.ProcessUserLocation(req)
		if err != nil {
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