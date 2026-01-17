# Stage 1: Build stage
# Sử dụng golang alpine để build cho nhẹ
FROM golang:1.21-alpine AS builder

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy go.mod và go.sum trước để tận dụng Docker cache layers
COPY go.mod go.sum ./

# Download các dependencies
RUN go mod download

# Copy toàn bộ source code vào image
COPY . .

# Build ứng dụng
# CGO_ENABLED=0: Build static binary (không phụ thuộc thư viện C của OS)
# -ldflags="-w -s": Loại bỏ debug info để giảm kích thước file binary
# cmd/server/main.go: Đường dẫn tới file main của bạn
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o media-service-app cmd/server/main.go

# Stage 2: Run stage
# Sử dụng alpine image nhỏ gọn để chạy ứng dụng
FROM alpine:latest

WORKDIR /app

# Cài đặt CA certificates để gọi HTTPS (cần thiết nếu MinIO dùng SSL hoặc gọi API ngoài)
RUN apk --no-cache add ca-certificates

# Copy file binary từ stage builder sang
COPY --from=builder /app/media-service-app .

# Expose port 8080
EXPOSE 8080

# Chạy ứng dụng
CMD ["./media-service-app"]