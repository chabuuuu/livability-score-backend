package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	ServerPort      string
	Environment     string
	MinioEndpoint   string
	MinioAccessKey  string
	MinioSecretKey  string
	MinioUseSSL     bool
	MediaServiceUrl string
	ImageBucket     string
	VideoBucket     string
}

var GlobalConfig *Config

func LoadConfig() {
	// Load .env file nếu tồn tại
	_ = godotenv.Load()

	GlobalConfig = &Config{
		ServerPort:      getEnv("PORT", "8080"),
		Environment:     getEnv("NODE_ENV", "prod"),
		MinioEndpoint:   getEnv("MINIO_ENDPOINT", "localhost:9000"),
		MinioAccessKey:  getEnv("MINIO_ACCESS_KEY", "minioadmin"),
		MinioSecretKey:  getEnv("MINIO_SECRET_KEY", "minioadmin"),
		MinioUseSSL:     getEnv("MINIO_USE_SSL", "false") == "true",
		MediaServiceUrl: getEnv("MEDIA_SERVICE_URL", "http://localhost:9000"),
		ImageBucket:     getEnv("MINIO_IMAGE_BUCKET", "images"),
		VideoBucket:     getEnv("MINIO_VIDEO_BUCKET", "videos"),
	}

	log.Printf("Config loaded: Environment=%s, Port=%s", GlobalConfig.Environment, GlobalConfig.ServerPort)
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}