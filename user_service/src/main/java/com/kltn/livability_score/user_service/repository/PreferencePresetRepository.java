package com.kltn.livability_score.user_service.repository;

import com.kltn.livability_score.user_service.entity.PreferencePresetEntity;
import java.math.BigDecimal;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PreferencePresetRepository extends JpaRepository<PreferencePresetEntity, Long> {

  Optional<PreferencePresetEntity> findByPreferenceEducationAndPreferenceSafetyAndPreferenceTransportationAndPreferenceShoppingAndPreferenceEntertainmentAndPreferenceEnvironmentAndPreferenceHealthcare(
      BigDecimal preferenceEducation, BigDecimal preferenceSafety,
      BigDecimal preferenceTransportation,
      BigDecimal preferenceShopping, BigDecimal preferenceEntertainment,
      BigDecimal preferenceEnvironment,
      BigDecimal preferenceHealthcare);
}