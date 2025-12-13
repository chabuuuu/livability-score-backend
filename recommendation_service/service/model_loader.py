import joblib
import os
import pandas as pd
from minio import Minio
from minio.error import S3Error

# --- CẤU HÌNH MINIO TỪ BIẾN MÔI TRƯỜNG ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000") # Docker service name
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "models")
MINIO_MODEL_FILE = os.getenv("MODEL_FILENAME", "sale_price_predictor_rf_2.joblib")

# Đường dẫn lưu file trong Container
MODEL_DIR = "model_files"
MODEL_PATH = os.path.join(MODEL_DIR, MINIO_MODEL_FILE)

class PriceModel:
    _model = None

    @staticmethod
    def _download_from_minio():
        """Hàm nội bộ để tải file từ MinIO về local storage."""
        print(f"⬇️ [AI] Model not found at {MODEL_PATH}. Attempting download from MinIO...")
        
        # 1. Đảm bảo thư mục tồn tại
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)

        try:
            # 2. Khởi tạo MinIO Client
            client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=True
            )

            # 3. Kiểm tra Bucket có tồn tại không
            if not client.bucket_exists(MINIO_BUCKET):
                print(f"❌ [MinIO] Bucket '{MINIO_BUCKET}' does not exist.")
                return False

            # 4. Tải file về
            client.fget_object(MINIO_BUCKET, MINIO_MODEL_FILE, MODEL_PATH)
            print(f"✅ [MinIO] Successfully downloaded '{MINIO_MODEL_FILE}' to '{MODEL_PATH}'")
            return True

        except S3Error as err:
            print(f"❌ [MinIO] S3 Error: {err}")
        except Exception as e:
            print(f"❌ [MinIO] Connection Error: {e}")
        
        return False

    @classmethod
    def load_model(cls):
        """Load model vào bộ nhớ một lần duy nhất."""
        if cls._model is None:
            # --- START MINIO INTEGRATION ---
            # Nếu file chưa tồn tại local, thử tải từ MinIO
            if not os.path.exists(MODEL_PATH):
                success = cls._download_from_minio()
                if not success:
                    print("⚠️ [AI] Could not download model. Prediction will fail.")
                    return # Dừng lại nếu không có file
            # --- END MINIO INTEGRATION ---

            # Logic load file gốc
            if os.path.exists(MODEL_PATH):
                try:
                    cls._model = joblib.load(MODEL_PATH)
                    print(f"✅ [AI] Loaded Price Prediction Model from {MODEL_PATH}")
                except Exception as e:
                    print(f"❌ [AI] Failed to load model with joblib: {e}")
            else:
                print(f"⚠️ [AI] Model file still not found at {MODEL_PATH}.")
    
    @classmethod
    def predict(cls, df: pd.DataFrame) -> float:
        """Thực hiện dự đoán giá."""
        if cls._model is None:
            # Thử load lại nếu chưa có (lazy load fallback)
            cls.load_model()
            if cls._model is None:
                # Tùy chọn: Trả về giá trị mặc định hoặc Raise lỗi
                raise Exception("Price Prediction Model is not loaded (MinIO download failed or file missing).")
        
        # Hàm predict của sklearn trả về mảng, ta lấy phần tử đầu tiên
        return cls._model.predict(df)[0]

# Tự động load khi import
PriceModel.load_model()