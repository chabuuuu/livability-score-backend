package controllers

import (
	"fmt"
	"media-service/internal/config"
	"media-service/internal/services"
	"media-service/internal/utils"
	"os"
	"path/filepath"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type MediaController struct {
	service *services.MediaService
}

func NewMediaController() *MediaController {
	return &MediaController{
		service: services.NewMediaService(),
	}
}

// Helper để lưu file tạm từ Gin Context
func saveTempFile(c *gin.Context, fileKey string) (string, string, error) {
	file, err := c.FormFile(fileKey)
	if err != nil {
		return "", "", err
	}

	// Tạo tên file unique để tránh trùng lặp trong temp folder
	ext := filepath.Ext(file.Filename)
	newFileName := uuid.New().String() + ext
	tempPath := filepath.Join(os.TempDir(), newFileName)

	if err := c.SaveUploadedFile(file, tempPath); err != nil {
		return "", "", err
	}

	return tempPath, newFileName, nil
}

func (ctrl *MediaController) UploadImage(c *gin.Context) {
	// Lưu file vào temp
	tempPath, fileName, err := saveTempFile(c, "file")
	if err != nil {
		utils.SendBadRequest(c, "No file uploaded or file save error")
		return
	}

	// Logic xử lý upload
	result, err := ctrl.service.UploadImage(tempPath, fileName)
	if err != nil {
		utils.SendError(c, 500, "Upload image failed")
		return
	}

	utils.SendOK(c, "Upload image successfully", result)
}

func (ctrl *MediaController) UploadVideo(c *gin.Context) {
	// Lưu file vào temp
	tempPath, fileName, err := saveTempFile(c, "file")
	if err != nil {
		utils.SendBadRequest(c, "No file uploaded or file save error")
		return
	}

	bucketName := config.GlobalConfig.VideoBucket
	
	// Chuẩn bị kết quả trả về ngay lập tức
	result := map[string]string{
		"mediaUrl": fmt.Sprintf("%s/%s/%s", config.GlobalConfig.MediaServiceUrl, bucketName, fileName),
	}

	// Gọi service upload dưới background (Fire and forget logic như Nodejs)
	ctrl.service.UploadVideoBackground(fileName, tempPath)

	utils.SendOK(c, "Upload video successfully", result)
}

func (ctrl *MediaController) GetVideoUrl(c *gin.Context) {
	result, err := ctrl.service.GetVideoUrl()
	if err != nil {
		utils.SendError(c, 500, "Get video url failed")
		return
	}
	utils.SendOK(c, "Get video url successfully", result)
}