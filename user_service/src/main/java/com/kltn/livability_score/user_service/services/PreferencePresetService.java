package com.kltn.livability_score.user_service.services;

import com.kltn.livability_score.user_service.model.preference_preset.request.PreferencePresetRequest;
import com.kltn.livability_score.user_service.model.preference_preset.response.PreferencePresetResponse;
import java.util.List;

public interface PreferencePresetService {

  // --- Admin Functions ---
  PreferencePresetResponse createPreset(PreferencePresetRequest request);

  PreferencePresetResponse updatePreset(Long id, PreferencePresetRequest request);

  void deletePreset(Long id);

  // --- Guest/Public Functions ---
  PreferencePresetResponse getPresetById(Long id);

  List<PreferencePresetResponse> getAllPresets();
}
