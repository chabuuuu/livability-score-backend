package database

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/go-redis/redis/v8"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// Global variables
var (
	DBProperties *gorm.DB
	DBScores     *gorm.DB
	RedisClient  *redis.Client
	Ctx          = context.Background()
)

// Helper: Đọc file CA và tạo TLS Config (Dùng cho Postgres hoặc các case cần custom CA)
func createTLSConfig(caCertPath string) (*tls.Config, error) {
	if caCertPath == "" {
		return nil, nil
	}
	caCert, err := os.ReadFile(caCertPath)
	if err != nil {
		return nil, fmt.Errorf("không thể đọc file CA tại %s: %v", caCertPath, err)
	}
	caCertPool := x509.NewCertPool()
	if ok := caCertPool.AppendCertsFromPEM(caCert); !ok {
		return nil, fmt.Errorf("không thể parse CA cert từ %s", caCertPath)
	}
	return &tls.Config{
		RootCAs:            caCertPool,
		MinVersion:         tls.VersionTLS12,
		InsecureSkipVerify: false,
	}, nil
}

// Helper: Append SSL params vào DSN Postgres
func buildPostgresDSN(originalDSN, caPath string) string {
	if originalDSN == "" {
		return ""
	}
	separator := "?"
	if strings.Contains(originalDSN, "?") {
		separator = "&"
	}
	// PostGIS/Postgres vẫn cần CA Path để verify nếu server yêu cầu
	sslParams := fmt.Sprintf("sslmode=verify-ca&sslrootcert=%s", caPath)
	return fmt.Sprintf("%s%s%s", originalDSN, separator, sslParams)
}

func Init() {
	sslCaPath := os.Getenv("SSL_CA_PATH")
	if sslCaPath == "" {
		sslCaPath = "ca.pem" // Fallback mặc định
	}

	// --- 1. Init Redis (Với SSL bật, không cần custom CA) ---
	redisHost := os.Getenv("REDIS_HOST")
	redisPort := os.Getenv("REDIS_PORT")
	redisUser := os.Getenv("REDIS_USER")
	redisPass := os.Getenv("REDIS_PASSWORD")

	if redisHost == "" { redisHost = "localhost" }
	if redisPort == "" { redisPort = "6379" }

	RedisClient = redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", redisHost, redisPort),
		Username: redisUser,
		Password: redisPass,
		DB:       0,
		// QUAN TRỌNG: Chỉ cần khai báo &tls.Config{} là SSL sẽ được bật.
		// Go sẽ tự động dùng System Cert Pool để verify server.
		TLSConfig: &tls.Config{
			MinVersion: tls.VersionTLS12,
		},
	})

	_, err := RedisClient.Ping(Ctx).Result()
	if err != nil {
		log.Fatal("❌ Không thể kết nối Redis:", err)
	}
	log.Println("✅ Redis connected successfully (SSL Enabled)")

	// --- 2. Init DB Properties ---
	propsDSN := os.Getenv("PROPERTY_DATABASE_URL")
	if propsDSN == "" {
		log.Fatal("❌ PROPERTY_DATABASE_URL is required")
	}
	finalPropsDSN := buildPostgresDSN(propsDSN, sslCaPath)

	DBProperties, err = gorm.Open(postgres.Open(finalPropsDSN), &gorm.Config{})
	if err != nil {
		log.Fatal("❌ Không thể kết nối DB Properties:", err)
	}
	log.Println("✅ DB Properties connected successfully")

	// --- 3. Init DB Scores ---
	scoresDSN := os.Getenv("SCORING_DATABASE_URL")
	if scoresDSN == "" {
		log.Fatal("❌ SCORING_DATABASE_URL is required")
	}
	finalScoresDSN := buildPostgresDSN(scoresDSN, sslCaPath)

	DBScores, err = gorm.Open(postgres.Open(finalScoresDSN), &gorm.Config{})
	if err != nil {
		log.Fatal("❌ Không thể kết nối DB Scores:", err)
	}
	log.Println("✅ DB Scores connected successfully")
}