package main

import (
	"log"
	"media-service/internal/config"
	"media-service/internal/routes"
	"media-service/internal/utils"
)

func main() {
	// 1. Load Config
	config.LoadConfig()

	// 2. Init MinIO
	utils.InitMinio()
	// Optional: Ensure buckets exist
	utils.EnsureBucketExists(config.GlobalConfig.ImageBucket)
	utils.EnsureBucketExists(config.GlobalConfig.VideoBucket)

	// 3. Setup Router
	r := routes.SetupRouter()

	// 4. Start Server
	port := config.GlobalConfig.ServerPort
	log.Printf("Server is running on http://localhost:%s in %s mode", port, config.GlobalConfig.Environment)
	
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}