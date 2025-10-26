package com.kltn.livability_score.user_service.exception.user;

import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum UserRegisterException implements ErrorCodeType {

  /**
   * Error User register exception.
   */
  USER_REGISTES_UserAlreadyExist("USER_REGISTES_UserAlreadyExist", "Người dùng đã tồn tại",
      HttpStatus.NOT_ACCEPTABLE),

  USER_REGISTER_CoolDown("USER_REGISTER_CoolDown",
      "The OTP was sent to your email recently. Please wait before requesting another.",
      HttpStatus.TOO_MANY_REQUESTS);

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
