package com.kltn.livability_score.user_service.repository;

import com.kltn.livability_score.user_service.entity.PreferencePresetEntity;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PreferencePresetRepository extends JpaRepository<PreferencePresetEntity, Long> {

  Optional<PreferencePresetEntity> findByPreferenceEducationAndPreferenceSafetyAndPreferenceTransportationAndPreferenceShoppingAndPreferenceEntertainmentAndPreferenceEnvironmentAndPreferenceHealthcare(
      Float preferenceEducation, Float preferenceSafety, Float preferenceTransportation,
      Float preferenceShopping, Float preferenceEntertainment, Float preferenceEnvironment,
      Float preferenceHealthcare);
}