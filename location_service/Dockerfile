# --- Stage 1: Builder (Dùng để compile code) ---
FROM golang:1.23-alpine AS builder

# Cài đặt git (nếu cần tải dependency từ private repo)
# RUN apk add --no-cache git

WORKDIR /app

# Copy file quản lý dependency trước để tận dụng layer caching của Docker
COPY go.mod go.sum ./
RUN go mod download

# Copy toàn bộ source code vào
COPY . .

# Build binary
# CGO_ENABLED=0: Build static binary (không phụ thuộc thư viện C của hệ thống)
# GOOS=linux: Target hệ điều hành Linux
RUN CGO_ENABLED=0 GOOS=linux go build -o location-service main.go

# --- Stage 2: Runner (Image nhẹ để chạy) ---
FROM alpine:latest

WORKDIR /root/

# Cài đặt CA Certificates (để gọi HTTPS/SSL) và Timezone
RUN apk --no-cache add ca-certificates tzdata

# Copy binary từ stage builder sang
COPY --from=builder /app/location-service .

RUN mkdir -p certs
COPY certs/ca.pem ./certs/ca.pem

# Copy file .env nếu muốn (thường thì nên inject qua environment variable của Docker/K8s an toàn hơn)
# COPY .env .

# Expose port
EXPOSE 8085

# Chạy ứng dụng
CMD ["./location-service"]