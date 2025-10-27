package com.kltn.livability_score.property_service.repository;

import com.kltn.livability_score.property_service.entity.PropertyEntity;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PropertyRepository extends JpaRepository<PropertyEntity, Long> {

  // Because of @Where, this already filters for deletedAt IS NULL
  @Override
  Optional<PropertyEntity> findById(Long id);

  // Find a property only if it belongs to the specific user
  Optional<PropertyEntity> findByIdAndUserId(Long id, Long userId);
}