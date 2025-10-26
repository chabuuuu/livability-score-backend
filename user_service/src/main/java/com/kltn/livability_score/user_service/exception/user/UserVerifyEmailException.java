package com.kltn.livability_score.user_service.exception.user;

import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum UserVerifyEmailException implements ErrorCodeType {

  /**
   * Error User register exception.
   */
  USER_VERIFY_EMAIL_InvalidOtp("USER_VERIFY_EMAIL_InvalidOtp",
      "Invalid OTP",
      HttpStatus.BAD_REQUEST);


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