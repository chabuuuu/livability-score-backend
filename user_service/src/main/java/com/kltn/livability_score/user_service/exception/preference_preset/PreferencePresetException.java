package com.kltn.livability_score.user_service.exception.preference_preset;


import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum PreferencePresetException implements ErrorCodeType {

  PRESET_NOT_FOUND("PRESET_NOT_FOUND", "Preference preset not found",
      HttpStatus.NOT_FOUND);

  final String value;
  final String description;
  final HttpStatus httpStatus;

  @Override
  public String getValue() {
    return value;
  }

  @Override
  public String getDescription() {
    return description;
  }

  @Override
  public HttpStatus getHttpStatus() {
    return httpStatus;
  }
}