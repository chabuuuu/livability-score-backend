package model

// Property map với bảng properties ở DB1
type Property struct {
	ID           int64   `gorm:"primaryKey"`
	Title        string
	AddressCity  string
	// Chúng ta sẽ lấy tọa độ bằng Raw SQL vì Gorm không hỗ trợ PostGIS native tốt mặc định
	Latitude     float64 `gorm:"-"` // Ignore field này khi query gorm thường
	Longitude    float64 `gorm:"-"`
}

// PropertyLivabilityScore map với bảng property_livability_scores ở DB2
type PropertyLivabilityScore struct {
	ID          int64 `gorm:"primaryKey"`
	PropertyID  int64
	// Giả sử logic tính điểm tổng hợp ở đây
	ScoreHealthcare     float64
	ScoreEducation      float64
	ScoreSafety         float64
    ScoreEnvironment    float64
}

// Request từ Mobile App gửi lên
type UserLocationRequest struct {
	UserID    string  `json:"-"`
	Latitude  float64 `json:"latitude" binding:"required"`
	Longitude float64 `json:"longitude" binding:"required"`
}