package com.kltn.livability_score.user_service.controllers;

import com.kltn.livability_score.user_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.user_service.exception.preference_preset.PreferencePresetException;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.user_service.model.preference_preset.request.PreferencePresetRequest;
import com.kltn.livability_score.user_service.model.preference_preset.response.PreferencePresetResponse;
import com.kltn.livability_score.user_service.services.PreferencePresetService;
import com.kltn.livability_score.user_service.utils.ResponseEntityGenerator;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/user/admin/preference-presets")
@RequiredArgsConstructor
@Tag(name = "Admin Preference Preset API", description = "Admin APIs for managing preference presets")
@SecurityRequirement(name = "bearerAuth") // Assume JWT auth
public class AdminPreferencePresetController {

  private final PreferencePresetService presetService;

  @PreAuthorize("hasAuthority('ADMIN')")
  @PostMapping
  @Operation(summary = "Create a new preference preset (Admin)")
  @ApiErrorResponse(errorEnum = PreferencePresetException.class) // Add validation errors
  public ResponseEntity<ResponseVO<PreferencePresetResponse>> createPreset(
      @Valid @RequestBody PreferencePresetRequest request) {

    PreferencePresetResponse response = presetService.createPreset(request);
    return ResponseEntityGenerator.okFormat(response);
  }

  @PreAuthorize("hasAuthority('ADMIN')")
  @PutMapping("/{id}")
  @Operation(summary = "Update an existing preference preset (Admin)")
  @ApiErrorResponse(errorEnum = PreferencePresetException.class)
  public ResponseEntity<ResponseVO<PreferencePresetResponse>> updatePreset(
      @PathVariable Long id,
      @Valid @RequestBody PreferencePresetRequest request) {

    PreferencePresetResponse response = presetService.updatePreset(id, request);
    return ResponseEntityGenerator.okFormat(response);
  }

  @PreAuthorize("hasAuthority('ADMIN')")
  @DeleteMapping("/{id}")
  @Operation(summary = "Delete a preference preset (Soft Delete) (Admin)")
  @ApiErrorResponse(errorEnum = PreferencePresetException.class)
  public ResponseEntity<ResponseVO<String>> deletePreset(
      @PathVariable Long id) {

    presetService.deletePreset(id);
    return ResponseEntityGenerator.okFormat("Deleted preference preset");
  }
}