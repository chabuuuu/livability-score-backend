from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import các router
from router import insight_router, livability_router, recommendation_router, amenity_router

app = FastAPI(title="Real Estate Recommendation Service")

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

if __name__ == "__main__":
    import uvicorn
    # Chạy server
    uvicorn.run(app, host="0.0.0.0", port=8084)