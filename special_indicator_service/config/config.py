import os
from dotenv import load_dotenv
import google.generativeai as genai
from itertools import cycle
from google.api_core import exceptions as google_exceptions
load_dotenv()

# --- GEMINI AI ---
KEYS_STR = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in KEYS_STR.split(",") if k.strip()]
key_cycle = cycle(API_KEYS)

def get_next_key():
    try: return next(key_cycle)
    except: raise Exception("No API Keys available")

FALLBACK_MODELS = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite", 
    "gemini-robotics-er-1.5-preview"
]

def generate_content_smart(prompt: str):
    last_error = None
    for model_name in FALLBACK_MODELS:
        for _ in range(4): # Retry 4 keys
            try:
                print(f"Trying to call Gemini model: {model_name}")
                current_key = get_next_key()
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel(model_name=model_name)
                response = model.generate_content(prompt, stream=False)
                
                return response
            except google_exceptions.ResourceExhausted:
                continue
            except Exception as e:
                last_error = e
                break
    raise last_error if last_error else Exception("AI Overloaded")

# --- DANH SÁCH QUẬN CẦN QUÉT ---
OSM_DISTRICT_QUERIES = [
    "District 1, Ho Chi Minh City, Vietnam",
    "District 3, Ho Chi Minh City, Vietnam",
    "District 4, Ho Chi Minh City, Vietnam",
    "District 5, Ho Chi Minh City, Vietnam",
    "District 6, Ho Chi Minh City, Vietnam",
    "District 7, Ho Chi Minh City, Vietnam",
    "District 8, Ho Chi Minh City, Vietnam",
    "District 10, Ho Chi Minh City, Vietnam",
    "District 11, Ho Chi Minh City, Vietnam",
    "District 12, Ho Chi Minh City, Vietnam",
    "Thủ Đức, Ho Chi Minh City, Vietnam",
    "Binh Thanh, Ho Chi Minh City, Vietnam",
    "Go Vap, Ho Chi Minh City, Vietnam",
    "Phu Nhuan, Ho Chi Minh City, Vietnam",
    "Tan Binh, Ho Chi Minh City, Vietnam",
    "Tan Phu, Ho Chi Minh City, Vietnam",
    "Binh Tan, Ho Chi Minh City, Vietnam",
    "Nha Be, Ho Chi Minh City, Vietnam",
    "Hoc Mon, Ho Chi Minh City, Vietnam",
    "Binh Chanh, Ho Chi Minh City, Vietnam",
    "Cu Chi, Ho Chi Minh City, Vietnam",
    "Can Gio, Ho Chi Minh City, Vietnam"
]

# Từ khóa tìm kiếm tin tức (Giữ nguyên)
KEYWORDS = {
    "flood": ["ngập lụt", "triều cường", "đường ngập", "chống ngập"],
    "accident": ["tai nạn giao thông", "điểm đen tai nạn", "kẹt xe nghiêm trọng"],
    "project": ["dự án metro", "mở rộng đường", "xây cầu mới", "quy hoạch công viên", "trung tâm thương mại sắp xây"]
}