-- 1. Tạo bảng property_livability_scores
CREATE TABLE IF NOT EXISTS property_livability_scores (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL UNIQUE,
    -- Unique để đảm bảo quan hệ 1-1 logic
    -- --- CHỈ SỐ THÔ (RAW METRICS) ---
    -- Lưu lại để phục vụ phân tích hoặc tính toán lại trọng số sau này
    dist_healthcare NUMERIC(10, 2),
    -- Khoảng cách đến y tế gần nhất (mét)
    dist_education NUMERIC(10, 2),
    -- Khoảng cách đến giáo dục gần nhất (mét)
    count_shopping INTEGER DEFAULT 0,
    -- Số lượng tiện ích mua sắm trong bán kính
    dist_transportation NUMERIC(10, 2),
    -- Khoảng cách đến giao thông công cộng (mét)
    dist_environment NUMERIC(10, 2),
    -- Khoảng cách đến công viên/không gian xanh (mét)
    count_entertainment INTEGER DEFAULT 0,
    -- Số lượng tiện ích giải trí trong bán kính
    dist_safety NUMERIC(10, 2),
    -- Khoảng cách đến đồn công an/PCCC (mét)
    -- --- ĐIỂM SỐ ĐÃ CHUẨN HÓA (NORMALIZED SCORES 0-100) ---
    score_healthcare NUMERIC(5, 2) DEFAULT 0,
    score_education NUMERIC(5, 2) DEFAULT 0,
    score_shopping NUMERIC(5, 2) DEFAULT 0,
    score_transportation NUMERIC(5, 2) DEFAULT 0,
    score_environment NUMERIC(5, 2) DEFAULT 0,
    score_entertainment NUMERIC(5, 2) DEFAULT 0,
    score_safety NUMERIC(5, 2) DEFAULT 0,
    -- Metadata thời gian
    create_at timestamp with time zone default now() not null,
    update_at timestamp with time zone default now() not null,
    delete_at timestamp with time zone
);