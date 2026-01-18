import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import redis
from dotenv import load_dotenv
import schedule
import time
import ssl

# --- Cấu hình ---
load_dotenv()
PROPERTY_DB_URL = os.getenv("PROPERTY_DATABASE_URL", "postgresql://avnadmin:password@host:port/defaultdb")
SSL_CA_PATH = os.getenv("SSL_CA_PATH", "ca.pem")
if not os.path.exists(SSL_CA_PATH):
    print(f"⚠️ Warning: SSL CA file not found at '{SSL_CA_PATH}'. Connection might fail.")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_USER = os.getenv("REDIS_USER", "default") # Redis 6+ dùng ACL, user mặc định thường là 'default'
ssl_context = ssl.create_default_context(cafile=SSL_CA_PATH)
ssl_context.check_hostname = False # Set True nếu muốn verify hostname chặt chẽ
ssl_context.verify_mode = ssl.CERT_REQUIRED

# --- Kết nối ---
db_connect_args = {
    "sslmode": "verify-ca", 
    "sslrootcert": SSL_CA_PATH
}

engine = create_engine(
    PROPERTY_DB_URL,
    connect_args=db_connect_args
)
r = redis.Redis(
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

def run_item_based_cf():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- [Worker] Bắt đầu tính toán Item-based CF ---")
    
    # 1. Load dữ liệu tương tác (User Favorites)
    print("1. Loading interaction data...")
    query = "SELECT user_id, property_id FROM user_favorite_properties"
    try:
        # Sử dụng connection từ engine để tránh lỗi connection closed nếu idle lâu
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
            
        if df.empty:
            print("   -> Không có dữ liệu tương tác. Kết thúc.")
            return
    except Exception as e:
        print(f"   -> Lỗi load DB: {e}")
        return

    # Thêm cột 'rating' mặc định là 1 (Implicit Feedback: Like = 1)
    df['rating'] = 1

    # 2. Tạo Ma trận User-Item
    print("2. Creating User-Item Matrix...")
    user_item_matrix = df.pivot_table(index='user_id', columns='property_id', values='rating').fillna(0)
    
    # Chuyển sang Sparse Matrix để tiết kiệm bộ nhớ và tính toán nhanh hơn
    sparse_user_item = csr_matrix(user_item_matrix.values)
    
    # 3. Tính độ tương đồng giữa các Item (Item-Item Similarity)
    print("3. Computing Item-Item Similarity...")
    item_similarity = cosine_similarity(sparse_user_item.T)
    item_similarity_df = pd.DataFrame(item_similarity, index=user_item_matrix.columns, columns=user_item_matrix.columns)

    # 4. Tạo gợi ý cho từng User
    print("4. Generating recommendations...")
    users = user_item_matrix.index.tolist()
    
    total_users = len(users)
    count = 0
    
    for user_id in users:
        try:
            # Lấy các item user này ĐÃ like
            user_likes = user_item_matrix.loc[user_id]
            liked_items = user_likes[user_likes > 0].index.tolist()
            
            if not liked_items:
                continue
                
            # Tính điểm cho các item CHƯA like
            sim_scores = item_similarity_df.loc[liked_items].sum().sort_values(ascending=False)
            
            # Loại bỏ các item user đã like rồi
            candidates = sim_scores.drop(index=liked_items)
            
            # Lấy Top 20 items có điểm cao nhất
            top_recommendations = candidates.head(20)
            
            # 5. Lưu vào Redis (Sorted Set)
            if not top_recommendations.empty:
                redis_key = f"rec:home:{user_id}"
                
                # Xóa cache cũ
                r.delete(redis_key)
                
                # Chuẩn bị mapping cho zadd
                mapping = {str(pid): score for pid, score in top_recommendations.items()}
                r.zadd(redis_key, mapping)
                
            count += 1
            if count % 100 == 0:
                print(f"   -> Processed {count}/{total_users} users")
                
        except Exception as e:
            print(f"   -> Lỗi xử lý user {user_id}: {e}")
            continue

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- [Worker] Hoàn tất tính toán Recommendation ---")

if __name__ == "__main__":
    # Chạy ngay một lần khi khởi động container/script
    print("Recommendation Worker Initializing...")
    run_item_based_cf()
    
    # Lên lịch chạy mỗi 1 tiếng
    schedule.every(1).hours.do(run_item_based_cf)
    
    print("Recommendation Worker Scheduler Started (Every 1 hour)...")
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Kiểm tra lịch mỗi phút