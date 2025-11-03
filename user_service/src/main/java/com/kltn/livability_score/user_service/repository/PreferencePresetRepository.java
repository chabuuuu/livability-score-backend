package com.kltn.livability_score.user_service.repository;

import com.kltn.livability_score.user_service.entity.PreferencePresetEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PreferencePresetRepository extends JpaRepository<PreferencePresetEntity, Long> {

}