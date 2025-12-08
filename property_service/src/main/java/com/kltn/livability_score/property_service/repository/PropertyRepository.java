package com.kltn.livability_score.property_service.repository;

import com.kltn.livability_score.property_service.entity.PropertyEntity;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.stereotype.Repository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

@Repository
public interface PropertyRepository extends JpaRepository<PropertyEntity, Long>,
    JpaSpecificationExecutor<PropertyEntity> {

  // Because of @Where, this already filters for deletedAt IS NULL
  @Override
  Optional<PropertyEntity> findById(Long id);

  // Find a property only if it belongs to the specific user
  Optional<PropertyEntity> findByIdAndUserId(Long id, Long userId);

  /**
   * Finds properties within a given bounding box (viewport).
   * We use a native query to leverage PostGIS functions.
   * ST_MakeEnvelope(minLng, minLat, maxLng, maxLat, 4326) creates the search box.
   * ST_Within(p.location, ...) checks if the property's location is inside that box.
   */
  @Query(value = "SELECT * FROM properties p " +
      "WHERE p.deleted_at IS NULL " + // IMPORTANT: Native queries bypass @Where
      "AND p.approval_status = 'APPROVED' " + // Only show approved properties
      "AND ST_Within(p.location, ST_MakeEnvelope(:minLng, :minLat, :maxLng, :maxLat, 4326))",
      nativeQuery = true)
  List<PropertyEntity> findPropertiesInViewport(
      @Param("minLat") double minLat,
      @Param("minLng") double minLng,
      @Param("maxLat") double maxLat,
      @Param("maxLng") double maxLng
  );

  @Modifying
  @Transactional
  @Query("UPDATE PropertyEntity p SET p.viewCount = COALESCE(p.viewCount, 0) + :amount WHERE p.id = :id")
  void incrementViewCountByAmount(@Param("id") Long id, @Param("amount") Long amount);
}