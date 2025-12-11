import redis
import os
import ssl
from dotenv import load_dotenv

load_dotenv()

SSL_CA_PATH = os.getenv("SSL_CA_PATH", "ca.pem")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USER = os.getenv("REDIS_USER", "default") # Redis 6+ dùng ACL, user mặc định thường là 'default'
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Cấu hình SSL Context cho Redis (Tuỳ chọn: Để kiểm soát chặt chẽ hơn việc verify)
# Nếu chỉ cần cơ bản, truyền ssl_ca_certs vào redis.Redis là đủ.
# Tuy nhiên, tạo context rõ ràng giúp debug dễ hơn.
ssl_context = ssl.create_default_context(cafile=SSL_CA_PATH)
ssl_context.check_hostname = False # Set True nếu muốn verify hostname chặt chẽ
ssl_context.verify_mode = ssl.CERT_REQUIRED

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USER,   # Thêm username
        password=REDIS_PASSWORD, # Thêm password
        decode_responses=True,
        ssl=True,              # Bật SSL
        ssl_ca_certs=SSL_CA_PATH, # File CA
        # ssl_cert_reqs="required", # Bắt buộc check cert
        socket_timeout=5       # Timeout để tránh treo app nếu Redis die
    )
    # Test kết nối ngay khi khởi động
    redis_client.ping()
    print("✅ Connected to Redis successfully via SSL!")
except redis.ConnectionError as e:
    print(f"❌ Failed to connect to Redis: {e}")