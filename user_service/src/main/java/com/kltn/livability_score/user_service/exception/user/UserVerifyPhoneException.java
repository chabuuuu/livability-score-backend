package com.kltn.livability_score.user_service.exception.user;

import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum UserVerifyPhoneException implements ErrorCodeType {

  /**
   * Error User register exception.
   */
  USER_VERIFY_PHONE_InvalidOtp("USER_VERIFY_PHONE_InvalidOtp",
      "Invalid OTP",
      HttpStatus.BAD_REQUEST),

  USER_VERIFY_PHONE_CoolDown("USER_VERIFY_PHONE_CoolDown",
      "The OTP was sent to your phone recently. Please wait before requesting another.",
      HttpStatus.TOO_MANY_REQUESTS),

  USER_VERIFY_PHONE_NotOwnPhone("USER_VERIFY_PHONE_NotOwnPhone",
      "User not own this phone",
      HttpStatus.BAD_REQUEST),

  USER_VERIFY_PHONE_SendSmsFailed("USER_VERIFY_PHONE_SendSmsFailed",
      "Can not send sms to this phone, please try again later",
      HttpStatus.INTERNAL_SERVER_ERROR),

  USER_VERIFY_PHONE_Verified("USER_VERIFY_PHONE_Verified",
      "User have verified this phone",
      HttpStatus.BAD_REQUEST),
  ;


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