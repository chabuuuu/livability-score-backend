import joblib
import os
import pandas as pd

# Đường dẫn tương đối từ thư mục gốc của project đến file model
MODEL_PATH = "model_files/sale_price_predictor_rf_2.joblib"

class PriceModel:
    _model = None

    @classmethod
    def load_model(cls):
        """Load model vào bộ nhớ một lần duy nhất."""
        if cls._model is None:
            if os.path.exists(MODEL_PATH):
                try:
                    cls._model = joblib.load(MODEL_PATH)
                    print(f"✅ [AI] Loaded Price Prediction Model from {MODEL_PATH}")
                except Exception as e:
                    print(f"❌ [AI] Failed to load model: {e}")
            else:
                print(f"⚠️ [AI] Model file not found at {MODEL_PATH}. Prediction will fail.")
    
    @classmethod
    def predict(cls, df: pd.DataFrame) -> float:
        """Thực hiện dự đoán giá."""
        if cls._model is None:
            # Thử load lại nếu chưa có (lazy load fallback)
            cls.load_model()
            if cls._model is None:
                raise Exception("Price Prediction Model is not loaded.")
        
        # Hàm predict của sklearn trả về mảng, ta lấy phần tử đầu tiên
        return cls._model.predict(df)[0]

# Tự động load khi import (hoặc gọi trong main.py startup event)
PriceModel.load_model()