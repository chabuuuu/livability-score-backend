package utils

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// SendOK gửi response thành công
func SendOK(c *gin.Context, message string, data interface{}) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": message,
		"data":    data,
	})
}

// SendBadRequest gửi response lỗi client
func SendBadRequest(c *gin.Context, message string) {
	c.JSON(http.StatusBadRequest, gin.H{
		"status":  "error",
		"message": message,
	})
}

// SendError gửi response lỗi server
func SendError(c *gin.Context, statusCode int, message string) {
	c.JSON(statusCode, gin.H{
		"status":  "error",
		"message": message,
	})
}