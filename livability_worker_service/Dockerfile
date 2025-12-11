# --- STAGE 1: Builder (Cài đặt dependencies) ---
FROM python:3.10-slim-bookworm as builder

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết để build Python packages
# libpq-dev cần thiết cho psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. Tạo virtual environment tại /opt/venv
RUN python -m venv /opt/venv

# 2. Kích hoạt venv bằng cách thêm vào PATH
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# 3. Cài đặt thư viện vào venv
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: Runner (Môi trường chạy thực tế) ---
FROM python:3.10-slim-bookworm

WORKDIR /app

# Cài đặt thư viện runtime cho Postgres (libpq5)
# curl dùng để healthcheck (nếu cần)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy toàn bộ venv từ builder sang runner
COPY --from=builder /opt/venv /opt/venv

# 5. Thiết lập PATH để sử dụng venv mặc định
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code của ứng dụng vào
COPY . .

# 6. Tạo user và phân quyền (Security Best Practice)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Tối ưu hóa Python
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1

# Lệnh chạy mặc định là worker.py
CMD ["python", "worker.py"]