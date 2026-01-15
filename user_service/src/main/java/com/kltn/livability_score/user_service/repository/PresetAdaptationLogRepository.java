package com.kltn.livability_score.user_service.repository;

import com.kltn.livability_score.user_service.entity.PresetAdaptationLogEntity;
import com.kltn.livability_score.user_service.model.preference_preset.response.PresetSuggestionResponse;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface PresetAdaptationLogRepository extends
    JpaRepository<PresetAdaptationLogEntity, Long> {

  @Query(
      "SELECT new com.kltn.livability_score.user_service.model.preference_preset.response.PresetSuggestionResponse("
          +
          "p.name, COUNT(l), " +
          "AVG(l.newSafety), AVG(l.newEducation), AVG(l.newShopping), " +
          "AVG(l.newTransportation), AVG(l.newEnvironment), " +
          "AVG(l.newEntertainment), AVG(l.newHealthcare)) " +
          "FROM PresetAdaptationLogEntity l " +
          "JOIN l.preferencePresetEntity p " +
          "WHERE p.id = :presetId " +
          "GROUP BY p.name")
  PresetSuggestionResponse getSuggestionStats(@Param("presetId") Long presetId);
}
