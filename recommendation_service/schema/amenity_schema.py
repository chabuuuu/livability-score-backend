from pydantic import BaseModel
from typing import Optional

class AmenityDTO(BaseModel):
    id: int
    name: str
    category: Optional[str]
    amenity_type: Optional[str]
    latitude: float
    longitude: float
    vicinity: Optional[str]
    google_rating: Optional[float]
    google_user_ratings_total: Optional[int]
    google_types: Optional[str]
    google_place_id: Optional[str]
    district: Optional[str]
    all_tags: Optional[str]

    class Config:
        from_attributes = True