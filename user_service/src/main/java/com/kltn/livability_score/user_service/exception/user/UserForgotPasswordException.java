package com.kltn.livability_score.user_service.exception.user;

import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum UserForgotPasswordException implements ErrorCodeType {

  /**
   * Error User register exception.
   */

  USER_FORGOT_PASSWORD_CoolDown("USER_FORGOT_PASSWORD_CoolDown",
      "The OTP was sent to your email recently. Please wait before requesting another.",
      HttpStatus.TOO_MANY_REQUESTS),

  USER_FORGOT_PASSWORD_InvalidOtp("USER_FORGOT_PASSWORD_InvalidOtp",
      "Invalid OTP",
      HttpStatus.BAD_REQUEST),

  USER_FORGOT_PASSWORD_UserNotFound(
      "USER_FORGOT_PASSWORD_UserNotFound", "User not exists", HttpStatus.NOT_FOUND);


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