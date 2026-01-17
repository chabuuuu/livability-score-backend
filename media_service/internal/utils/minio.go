package utils

import (
	"context"
	"log"
	"media-service/internal/config"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

var MinioClient *minio.Client

func InitMinio() {
	var err error
	MinioClient, err = minio.New(config.GlobalConfig.MinioEndpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(config.GlobalConfig.MinioAccessKey, config.GlobalConfig.MinioSecretKey, ""),
		Secure: config.GlobalConfig.MinioUseSSL,
	})

	if err != nil {
		log.Fatalf("Failed to initialize MinIO client: %v", err)
	}

	log.Println("MinIO client initialized successfully")
}

func EnsureBucketExists(bucketName string) {
	ctx := context.Background()
	exists, err := MinioClient.BucketExists(ctx, bucketName)
	if err != nil {
		log.Printf("Error checking bucket %s: %v", bucketName, err)
		return
	}
	if !exists {
		err = MinioClient.MakeBucket(ctx, bucketName, minio.MakeBucketOptions{})
		if err != nil {
			log.Printf("Error creating bucket %s: %v", bucketName, err)
		} else {
			log.Printf("Bucket created: %s", bucketName)
		}
	}
}