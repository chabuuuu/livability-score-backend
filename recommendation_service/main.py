from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

# Import class PriceModel từ file utils
from service.model_loader import PriceModel

# Import các router
from router import insight_router, livability_router, prediction_router, recommendation_router, amenity_router

# --- CẤU HÌNH LIFESPAN (STARTUP EVENT) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Xử lý các tác vụ khi server khởi động và tắt.
    """
    # 1. STARTUP: Gọi load model trong background (không await)
    # Sử dụng create_task để server khởi động ngay lập tức mà không cần chờ tải xong model 500MB
    print("🚀 [System] Triggering background model download...")
    asyncio.create_task(PriceModel.load_model())
    
    yield
    
    # 2. SHUTDOWN: Dọn dẹp nếu cần (ví dụ đóng connect db)
    print("🛑 [System] Shutting down...")

app = FastAPI(
    title="Real Estate Recommendation Service",
    lifespan=lifespan # Đăng ký lifespan vào app
)

# Cấu hình CORS (Cho phép Frontend gọi API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong production nên set domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router
app.include_router(recommendation_router.router)
app.include_router(amenity_router.router)
app.include_router(livability_router.router)
app.include_router(insight_router.router)
app.include_router(prediction_router.router)

if __name__ == "__main__":
    import uvicorn
    # Chạy server
    uvicorn.run(app, host="0.0.0.0", port=8084)