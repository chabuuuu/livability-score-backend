package services

import (
	"context"
	"fmt"
	"log"
	"media-service/internal/config"
	"media-service/internal/utils"
	"os"

	"github.com/google/uuid"
	"github.com/minio/minio-go/v7"
)

type MediaService struct{}

func NewMediaService() *MediaService {
	return &MediaService{}
}

type MediaUploadRes struct {
	MediaUrl string `json:"mediaUrl"`
}

type GetMediaUrlRes struct {
	MediaUrl string `json:"mediaUrl"`
	FileName string `json:"fileName"`
}

func (s *MediaService) UploadImage(tempFilePath string, fileName string) (*MediaUploadRes, error) {
	bucketName := config.GlobalConfig.ImageBucket

	// Upload file to MinIO
	_, err := utils.MinioClient.FPutObject(context.Background(), bucketName, fileName, tempFilePath, minio.PutObjectOptions{
		ContentType: "image/jpeg",
	})

	// Xóa file tạm bất kể thành công hay thất bại (defer hoặc ngay sau khi xong)
	defer func() {
		if err := os.Remove(tempFilePath); err != nil {
			log.Printf("Error deleting temp file %s: %v", tempFilePath, err)
		}
	}()

	if err != nil {
		log.Printf("Failed to upload image: %v", err)
		return nil, err
	}

	return &MediaUploadRes{
		MediaUrl: fmt.Sprintf("%s/%s/%s", config.GlobalConfig.MediaServiceUrl, bucketName, fileName),
	}, nil
}

func (s *MediaService) UploadVideoBackground(fileName string, tempFilePath string) {
	bucketName := config.GlobalConfig.VideoBucket

	// Chạy trong Goroutine để không block request chính
	go func() {
		defer func() {
			// Xóa file tạm sau khi xử lý xong
			if err := os.Remove(tempFilePath); err != nil {
				log.Printf("Error deleting temp file %s: %v", tempFilePath, err)
			}
		}()

		log.Printf("Starting background upload for video: %s", fileName)
		_, err := utils.MinioClient.FPutObject(context.Background(), bucketName, fileName, tempFilePath, minio.PutObjectOptions{
			ContentType: "video/mp4", // Hoặc detect động
		})

		if err != nil {
			log.Printf("Failed to upload video background %s: %v", fileName, err)
			return
		}
		log.Printf("Successfully uploaded video background: %s", fileName)
	}()
}

func (s *MediaService) GetVideoUrl() (*GetMediaUrlRes, error) {
	bucketName := config.GlobalConfig.VideoBucket
	fileName := uuid.New().String()

	return &GetMediaUrlRes{
		MediaUrl: fmt.Sprintf("%s/%s/%s", config.GlobalConfig.MediaServiceUrl, bucketName, fileName),
		FileName: fileName,
	}, nil
}