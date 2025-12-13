import joblib
import os
import sys
import zipfile
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

    @staticmethod
    def _download_and_extract():
        """Tải file zip từ MinIO và giải nén."""
        print(f"⬇️ [AI] Model not found at {MODEL_PATH}. Checking MinIO for archive '{MINIO_ARCHIVE_FILE}'...")
        
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)

        try:
            client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )

            if not client.bucket_exists(MINIO_BUCKET):
                print(f"❌ [MinIO] Bucket '{MINIO_BUCKET}' does not exist.")
                return False

            # --- TỐI ƯU HÓA DOWNLOAD ---
            # Thay vì gọi stat_object (gây chậm), ta gọi get_object luôn.
            # Lấy size từ header của response stream.
            print(f"⬇️ [MinIO] Requesting '{MINIO_ARCHIVE_FILE}'...")
            
            response = None
            try:
                response = client.get_object(MINIO_BUCKET, MINIO_ARCHIVE_FILE)
                
                # Lấy Content-Length từ header ngay lập tức
                total_size = int(response.headers.get('content-length', 0))
                print(f"⬇️ [MinIO] Stream started. Total size: {total_size} bytes")
                
                current_size = 0
                chunk_size = 32 * 1024 # 32KB chunks

                # Tự ghi file và update progress bar thủ công
                with open(ARCHIVE_PATH, 'wb') as file_data:
                    for data in response.stream(chunk_size):
                        file_data.write(data)
                        current_size += len(data)
                        
                        # Update progress bar
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
                    # Kiểm tra xem file model cần thiết có trong zip không
                    if REAL_MODEL_FILENAME not in zip_ref.namelist():
                         print(f"⚠️ [System] Warning: '{REAL_MODEL_FILENAME}' not found in zip archive!")
                         print(f"   Files in zip: {zip_ref.namelist()}")

                    zip_ref.extractall(MODEL_DIR)
                
                print(f"✅ [System] Extracted successfully to '{MODEL_DIR}'")
                
                # Xóa file zip cho nhẹ máy
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
    def load_model(cls):
        """Quy trình: Check Local -> Download Zip & Giải nén -> Load Model."""
        if cls._model is None:
            # 1. Kiểm tra nếu file joblib chưa có, thực hiện tải và giải nén
            if not os.path.exists(MODEL_PATH):
                success = cls._download_and_extract()
                if not success and not os.path.exists(MODEL_PATH):
                    print("⚠️ [AI] Could not setup model file. Prediction will fail.")
                    return

            # 2. Load file model thật (joblib)
            if os.path.exists(MODEL_PATH):
                try:
                    cls._model = joblib.load(MODEL_PATH)
                    print(f"✅ [AI] MODEL LOADED READY: {MODEL_PATH}")
                except Exception as e:
                    print(f"❌ [AI] Failed to load joblib file: {e}")
            else:
                print(f"❌ [AI] Model file '{REAL_MODEL_FILENAME}' not found. Please check MINIO_ARCHIVE_FILE and MODEL_FILENAME env vars.")
    
    @classmethod
    def predict(cls, df: pd.DataFrame) -> float:
        if cls._model is None:
            cls.load_model()
            if cls._model is None:
                raise Exception("Price Prediction Model is not available.")
        return cls._model.predict(df)[0]

# Auto load on start
PriceModel.load_model()