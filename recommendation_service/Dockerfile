# --- STAGE 1: Builder (Cài đặt dependencies) ---
FROM python:3.10-slim as builder

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết để build Python packages
# libpq-dev cần thiết để compile psycopg2 (nếu dùng bản source)
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
    && rm -rf /var/lib/apt/lists/*

# Copy thư viện đã cài từ stage builder sang
COPY --from=builder /root/.local /root/.local

# Đảm bảo biến môi trường PATH nhận diện được thư viện vừa copy
ENV PATH=/root/.local/bin:$PATH

# Copy source code của ứng dụng vào
COPY . .

# Copy file chứng chỉ CA nếu cần thiết (đảm bảo file này nằm cùng thư mục build)
# COPY /certs /app/certs 

# Tối ưu hóa Python cho container
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1

# Expose port (Chỉ mang tính chất tài liệu, uvicorn sẽ listen port này)
EXPOSE 8084

# Lệnh chạy: Sử dụng uvicorn trực tiếp thay vì python main.py
# --workers 4: Chạy đa luồng (Production nên set workers = số CPU core * 2 + 1)
# --proxy-headers: Quan trọng nếu chạy sau Nginx/Traefik
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084", "--workers", "4", "--proxy-headers"]