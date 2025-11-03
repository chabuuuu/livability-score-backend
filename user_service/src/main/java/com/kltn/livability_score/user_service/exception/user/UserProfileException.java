package com.kltn.livability_score.user_service.exception.user;

import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum UserProfileException implements ErrorCodeType {

  PROFILE_NOT_FOUND("PROFILE_NOT_FOUND", "User profile not found",
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