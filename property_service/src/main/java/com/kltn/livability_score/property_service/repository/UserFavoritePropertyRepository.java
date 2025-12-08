package com.kltn.livability_score.property_service.repository;

import com.kltn.livability_score.property_service.entity.PropertyEntity;
import com.kltn.livability_score.property_service.entity.UserFavoritePropertyEntity;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface UserFavoritePropertyRepository extends
    JpaRepository<UserFavoritePropertyEntity, Long>, JpaSpecificationExecutor<UserFavoritePropertyEntity> {

  // Tìm kiếm dựa trên userId và propertyId
  // Nhờ BaseEntity có @Where(deleted_at is null), nó chỉ tìm những cái chưa xóa (đang thích)
  Optional<UserFavoritePropertyEntity> findByUserIdAndPropertyId(Long userId, Long propertyId);

  boolean existsByUserIdAndPropertyId(Long userId, Long propertyId);
}