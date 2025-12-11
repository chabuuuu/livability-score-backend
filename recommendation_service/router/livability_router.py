from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from config.scoring_db_config import get_scoring_db
from model.livability_score import PropertyLivabilityScore
from schema.common import APIResponse, ResponseData
from schema.livability_schema import LivabilityScoreDTO, BatchScoreRequest

router = APIRouter(prefix="/api/v1/recommendation/livability", tags=["Livability Scores"])

# Trọng số mặc định (Sau này có thể thay thế bằng Profile User)
DEFAULT_WEIGHTS = {
    'score_healthcare': 0.15,
    'score_education': 0.15,
    'score_shopping': 0.15,
    'score_transportation': 0.15,
    'score_environment': 0.15,
    'score_entertainment': 0.15,
    'score_safety': 0.10,
}

def calculate_overall_score(score_obj: PropertyLivabilityScore, weights: dict) -> float:
    """Hàm helper tính điểm tổng hợp từ object SQLAlchemy"""
    total_score = 0.0
    
    # Hàm an toàn để lấy giá trị (xử lý None thành 0.0)
    def get_val(val):
        return float(val) if val is not None else 0.0

    total_score += get_val(score_obj.score_healthcare) * weights['score_healthcare']
    total_score += get_val(score_obj.score_education) * weights['score_education']
    total_score += get_val(score_obj.score_shopping) * weights['score_shopping']
    total_score += get_val(score_obj.score_transportation) * weights['score_transportation']
    total_score += get_val(score_obj.score_environment) * weights['score_environment']
    total_score += get_val(score_obj.score_entertainment) * weights['score_entertainment']
    total_score += get_val(score_obj.score_safety) * weights['score_safety']

    return round(total_score, 2)

@router.post("/scores/batch", response_model=APIResponse[LivabilityScoreDTO])
def get_batch_livability_scores(
    payload: BatchScoreRequest,
    db: Session = Depends(get_scoring_db)
):
    try:
        if not payload.propertyIds:
            return APIResponse(status="200", result="Succeeded", data=ResponseData(items=[]))

        scores = db.query(PropertyLivabilityScore).filter(
            PropertyLivabilityScore.property_id.in_(payload.propertyIds),
            PropertyLivabilityScore.delete_at.is_(None)
        ).all()

        results = []
        for score_record in scores:
            # 1. Convert SQLAlchemy Model sang Pydantic Model (chưa có livability_score)
            dto = LivabilityScoreDTO.model_validate(score_record)
            
            # 2. Tính toán điểm tổng hợp (Dùng Default Weights)
            # (Sau này: Lấy user_id từ request -> query profile -> lấy weights custom -> truyền vào đây)
            final_score = calculate_overall_score(score_record, DEFAULT_WEIGHTS)
            
            # 3. Gán điểm vào DTO
            dto.livability_score = final_score
            results.append(dto)

        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=results)
        )

    except Exception as e:
        print(f"Error fetching batch scores: {e}")
        return APIResponse(status="500", result="Failed", error=str(e))