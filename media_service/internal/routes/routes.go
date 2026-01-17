package routes

import (
	"media-service/internal/controllers"
	"net/http"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func SetupRouter() *gin.Engine {
	r := gin.Default() 

	// Config CORS 
	corsConfig := cors.DefaultConfig()
	corsConfig.AllowAllOrigins = true // Customize theo GlobalConfig của bạn
	corsConfig.AllowHeaders = []string{"Origin", "Content-Length", "Content-Type", "Authorization"}
	r.Use(cors.New(corsConfig))


	// Max Multipart Memory (Giới hạn RAM khi upload, phần dư sẽ ghi xuống disk)
	r.MaxMultipartMemory = 8 << 20 // 8 MiB (đủ cho buffer, file lớn sẽ stream xuống temp)

	mediaCtrl := controllers.NewMediaController()

	v1 := r.Group("/api/v1/media")
	{
		v1.POST("/upload-image", mediaCtrl.UploadImage)
		v1.POST("/upload-video", mediaCtrl.UploadVideo)
		v1.GET("/video-url", mediaCtrl.GetVideoUrl)
	}

	// Health Check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "OK"})
	})

	// Handle API not exists
	r.NoRoute(func(c *gin.Context) {
		c.JSON(http.StatusNotFound, gin.H{"message": "API not exists"})
	})

	return r
}