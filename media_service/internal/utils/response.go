package utils

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Response cấu trúc JSON trả về thống nhất
type Response struct {
	Status  string      `json:"status"`
	Code    int         `json:"code"`
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data"`
	Errors  interface{} `json:"errors"`
}

// SendOK gửi response thành công
func SendOK(c *gin.Context, message string, data interface{}) {
	c.JSON(http.StatusOK, Response{
		Status:  "OK",
		Code:    http.StatusOK,
		Success: true,
		Message: message,
		Data:    data,
		Errors:  nil,
	})
}

// SendBadRequest gửi response lỗi client (400)
func SendBadRequest(c *gin.Context, message string) {
	c.JSON(http.StatusBadRequest, Response{
		Status:  "BAD_REQUEST",
		Code:    http.StatusBadRequest,
		Success: false,
		Message: message,
		Data:    nil,
		Errors:  message,
	})
}

// SendError gửi response lỗi server hoặc các lỗi khác
func SendError(c *gin.Context, statusCode int, message string) {
	statusStr := "ERROR"
	switch statusCode {
	case http.StatusNotFound:
		statusStr = "NOT_FOUND"
	case http.StatusUnauthorized:
		statusStr = "UNAUTHORIZED"
	case http.StatusForbidden:
		statusStr = "FORBIDDEN"
	}

	c.JSON(statusCode, Response{
		Status:  statusStr,
		Code:    statusCode,
		Success: false,
		Message: message,
		Data:    nil,
		Errors:  message,
	})
}