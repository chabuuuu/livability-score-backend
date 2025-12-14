# --- STAGE 1: Builder (Cài đặt dependencies) ---
FROM python:3.10-slim as builder

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết để build Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt
COPY requirements.txt .

# --user: Cài đặt vào thư mục local của user để dễ copy sang stage sau
# --no-cache-dir: Không lưu cache pip để giảm dung lượng
RUN pip install --user --no-cache-dir -r requirements.txt

# --- STAGE 2: Runner (Môi trường chạy thực tế) ---
FROM python:3.10-slim

WORKDIR /app

# Chỉ cài libpq5 (runtime) chứ không cài compiler
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \ 
    && rm -rf /var/lib/apt/lists/*

# Copy thư viện đã cài từ stage builder sang
COPY --from=builder /root/.local /root/.local

# Đảm bảo biến môi trường PATH nhận diện được thư viện vừa copy
ENV PATH=/root/.local/bin:$PATH

# Copy source code của ứng dụng vào
COPY . .

# Tối ưu hóa Python cho container
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8084

# --- LỆNH CHẠY TỐI ƯU HÓA (RAM SHARING) ---
# 1. python preload_model.py: Tải file model về đĩa nếu chưa có (Single process).
# 2. gunicorn ... --preload: Load code & Model vào RAM ở Master Process, sau đó fork ra 3 workers.
#    Các worker sẽ dùng chung vùng nhớ model này -> Tiết kiệm RAM.
# --timeout 900: Tăng thời gian chờ khởi động (đề phòng load model lâu).
# --access-logfile -: Đẩy log ra stdout để Docker hiển thị.

CMD ["sh", "-c", "python preload_model.py && gunicorn main:app --bind 0.0.0.0:8084 --workers 3 --worker-class uvicorn.workers.UvicornWorker --preload --timeout 900 --access-logfile - --error-logfile -"]