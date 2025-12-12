import os
import json
import redis
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from calculator import LivabilityCalculator
from config.property_service_db_config import get_property_service_db
from config.scoring_service_db_config import get_scoring_service_db

# Load config
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USER = os.getenv("REDIS_USER", "default") # Redis 6+ dùng ACL, user mặc định thường là 'default'
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")


REDIS_CHANNEL = "property_updates" # Channel để lắng nghe


def process_message(message_data):
    """Xử lý message nhận được từ Redis"""
    scoring_db = get_scoring_service_db()
    property_db = get_property_service_db()
    calculator = LivabilityCalculator(property_db, scoring_db)

    try:
        print(f"Received message: {message_data}")
        data = json.loads(message_data)
        property_id = data.get("property_id")
        action = data.get("action") # 'created', 'updated'
        
        if property_id:
            print(f"Received event: {action} for Property {property_id}")
            calculator.calculate_for_property(property_id)
        else:
            print("Invalid message format: missing property_id")
            
    except Exception as e:
        print(f"Error processing message: {e}")
    finally:
        scoring_db.close()
        property_db.close()

def main():
    # Setup Redis
    try:
        r = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            username=REDIS_USER,   # Thêm username
            password=REDIS_PASSWORD, 
            decode_responses=True,
            ssl=True,              # Bật SSL
            socket_timeout=None,       # Timeout để tránh treo app nếu Redis die
            socket_keepalive=True,      # Giữ kết nối luôn sống
            health_check_interval=30  # Kiểm tra sức khỏe kết nối mỗi 30 giây
        )
        pubsub = r.pubsub()
        pubsub.subscribe(REDIS_CHANNEL)
        
        print(f"Livability Ingestion Service started. Listening on '{REDIS_CHANNEL}'...")

        for message in pubsub.listen():
            if message['type'] == 'message':
                process_message(message['data'])
                
    except redis.ConnectionError as e:
        print(f"Redis connection failed: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)
        main() # Retry connection
    except KeyboardInterrupt:
        print("Stopping worker...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Quan trọng: Nếu worker sập, restart lại sau 5s thay vì tắt hẳn
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()