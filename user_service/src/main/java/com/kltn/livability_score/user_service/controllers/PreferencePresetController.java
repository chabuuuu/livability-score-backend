package com.kltn.livability_score.user_service.controllers;


import com.kltn.livability_score.user_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.user_service.exception.preference_preset.PreferencePresetException;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.user_service.model.preference_preset.response.PreferencePresetResponse;
import com.kltn.livability_score.user_service.model.preference_preset.response.PresetSuggestionResponse;
import com.kltn.livability_score.user_service.services.PreferencePresetService;
import com.kltn.livability_score.user_service.utils.ResponseEntityGenerator;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/user/preference-presets")
@RequiredArgsConstructor
@Tag(name = "Preference Preset API", description = "Public APIs for viewing preference presets")
public class PreferencePresetController {

  private final PreferencePresetService presetService;

  @GetMapping
  @Operation(summary = "Get all available preference presets")
  public ResponseEntity<ResponseVO<List<PreferencePresetResponse>>> getAllPresets() {
    List<PreferencePresetResponse> response = presetService.getAllPresets();
    return ResponseEntityGenerator.okFormat(response);
  }

  @GetMapping("/{id}")
  @Operation(summary = "Get a single preference preset by ID")
  @ApiErrorResponse(errorEnum = PreferencePresetException.class)
  public ResponseEntity<ResponseVO<PreferencePresetResponse>> getPresetById(
      @PathVariable Long id) {
    PreferencePresetResponse response = presetService.getPresetById(id);
    return ResponseEntityGenerator.okFormat(response);
  }

  @GetMapping("/suggestion/{id}")
  @Operation(summary = "Get a single suggestion preference preset by ID")
  public ResponseEntity<ResponseVO<PresetSuggestionResponse>> getPresetSuggestion(
      @PathVariable Long id) {
    return ResponseEntityGenerator.okFormat(presetService.getSuggestionForPreset(id));
  }
}