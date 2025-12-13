import joblib
import os
import sys
import zipfile
import asyncio
import pandas as pd
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

load_dotenv()

# --- CẤU HÌNH MINIO TỪ BIẾN MÔI TRƯỜNG ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "models")

# Tên file nén trên MinIO (VD: model.zip)
MINIO_ARCHIVE_FILE = os.getenv("MINIO_ARCHIVE_FILE", "sale_price_predictor.zip")

# Tên file model thật nằm TRONG file nén (VD: sale_price_predictor_rf_2.joblib)
REAL_MODEL_FILENAME = os.getenv("MODEL_FILENAME", "sale_price_predictor_rf_2.joblib")

# --- ĐƯỜNG DẪN LOCAL ---
MODEL_DIR = "model_files"
ARCHIVE_PATH = os.path.join(MODEL_DIR, MINIO_ARCHIVE_FILE)
MODEL_PATH = os.path.join(MODEL_DIR, REAL_MODEL_FILENAME)

class PriceModel:
    _model = None
    _lock = asyncio.Lock()  # Lock để tránh Race Condition khi nhiều request cùng gọi load

    @staticmethod
    def _download_and_extract_sync():
        """
        Hàm đồng bộ (Blocking): Tải file zip từ MinIO và giải nén.
        Hàm này sẽ chạy trong Thread riêng.
        """
        print(f"⬇️ [AI] Model not found at {MODEL_PATH}. Checking MinIO for archive '{MINIO_ARCHIVE_FILE}'...")
        
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)

        try:
            client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=True
            )

            if not client.bucket_exists(MINIO_BUCKET):
                print(f"❌ [MinIO] Bucket '{MINIO_BUCKET}' does not exist.")
                return False

            # --- TỐI ƯU HÓA DOWNLOAD ---
            print(f"⬇️ [MinIO] Requesting '{MINIO_ARCHIVE_FILE}'...")
            
            response = None
            try:
                response = client.get_object(MINIO_BUCKET, MINIO_ARCHIVE_FILE)
                
                total_size = int(response.headers.get('content-length', 0))
                print(f"⬇️ [MinIO] Stream started. Total size: {total_size} bytes")
                
                current_size = 0
                chunk_size = 32 * 1024 

                with open(ARCHIVE_PATH, 'wb') as file_data:
                    for data in response.stream(chunk_size):
                        file_data.write(data)
                        current_size += len(data)
                        
                        if total_size > 0:
                            percent = (current_size / total_size) * 100
                            sys.stdout.write(f"\r⬇️ [MinIO] Downloading ZIP: {percent:.1f}% ({current_size}/{total_size})")
                            sys.stdout.flush()
                
                print("\n✅ [MinIO] Download complete.")

            except Exception as e:
                print(f"\n❌ [MinIO] Stream Error: {e}")
                return False
            finally:
                if response:
                    response.close()
                    response.release_conn()

            # --- 2. EXTRACT ZIP FILE ---
            print(f"📦 [System] Extracting '{ARCHIVE_PATH}'...")
            try:
                with zipfile.ZipFile(ARCHIVE_PATH, 'r') as zip_ref:
                    if REAL_MODEL_FILENAME not in zip_ref.namelist():
                         print(f"⚠️ [System] Warning: '{REAL_MODEL_FILENAME}' not found in zip archive!")
                         print(f"   Files in zip: {zip_ref.namelist()}")

                    zip_ref.extractall(MODEL_DIR)
                
                print(f"✅ [System] Extracted successfully to '{MODEL_DIR}'")
                
                if os.path.exists(ARCHIVE_PATH):
                    os.remove(ARCHIVE_PATH)
                    print(f"🗑️ [System] Removed temporary archive '{ARCHIVE_PATH}'")
                
                return True
            except zipfile.BadZipFile:
                print(f"❌ [System] Error: The downloaded file is not a valid zip file.")
                return False

        except S3Error as err:
            print(f"\n❌ [MinIO] S3 Error: {err}")
        except Exception as e:
            print(f"\n❌ [MinIO] General Error: {e}")
        
        return False

    @classmethod
    def _load_model_internal_sync(cls):
        """Hàm đồng bộ chứa logic nặng: Download & Load Joblib."""
        # 1. Kiểm tra và Download
        if not os.path.exists(MODEL_PATH):
            success = cls._download_and_extract_sync()
            if not success and not os.path.exists(MODEL_PATH):
                print("⚠️ [AI] Could not setup model file. Prediction will fail.")
                return None

        # 2. Load Joblib (CPU/Disk Bound)
        if os.path.exists(MODEL_PATH):
            try:
                model = joblib.load(MODEL_PATH)
                print(f"✅ [AI] MODEL LOADED READY: {MODEL_PATH}")
                return model
            except Exception as e:
                print(f"❌ [AI] Failed to load joblib file: {e}")
        else:
            print(f"❌ [AI] Model file '{REAL_MODEL_FILENAME}' not found. Please check env vars.")
        return None

    @classmethod
    async def load_model(cls):
        """
        Async version: Load model vào bộ nhớ.
        Sử dụng ThreadPool để không block event loop trong quá trình download/load.
        """
        if cls._model is not None:
            return

        async with cls._lock: # Đảm bảo chỉ 1 coroutine được tải model tại 1 thời điểm
            if cls._model is not None: # Double-check locking pattern
                return

            # Chạy logic đồng bộ trong thread riêng
            cls._model = await asyncio.to_thread(cls._load_model_internal_sync)

    @classmethod
    async def predict(cls, df: pd.DataFrame) -> float:
        """Async Predict."""
        if cls._model is None:
            await cls.load_model()
            if cls._model is None:
                raise Exception("Price Prediction Model is not available.")
        
        # Chạy dự đoán (CPU bound) trong thread riêng để không block request khác
        result = await asyncio.to_thread(cls._model.predict, df)
        return result[0]
