package com.kltn.livability_score.user_service.exception.user;


import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum UserRoleException implements ErrorCodeType {

  USER_NOT_FOUND("USER_NOT_FOUND", "User account not found",
      HttpStatus.NOT_FOUND),

  ALREADY_A_SELLER("ALREADY_A_SELLER", "You are already a seller",
      HttpStatus.BAD_REQUEST),

  REQUEST_ALREADY_PENDING("REQUEST_ALREADY_PENDING",
      "Your request is already pending approval",
      HttpStatus.BAD_REQUEST),

  PHONE_NOT_VERIFIED("PHONE_NOT_VERIFIED",
      "You must verify your phone number before requesting seller role",
      HttpStatus.BAD_REQUEST),

  /**
   * Old password provided does not match the stored password.
   */
  PASSWORD_INCORRECT("PASSWORD_INCORRECT",
      "The old password is not correct",
      HttpStatus.BAD_REQUEST),

  /**
   * New password cannot be the same as the old password.
   */
  PASSWORD_SAME_AS_OLD("PASSWORD_SAME_AS_OLD",
      "New password cannot be the same as the old password",
      HttpStatus.BAD_REQUEST),

  /**
   * Admin is trying to review a request that is not in PENDING state.
   */
  REQUEST_NOT_PENDING("REQUEST_NOT_PENDING",
      "This user does not have a pending request to review",
      HttpStatus.BAD_REQUEST),

  /**
   * Admin sent an invalid status (e.g., PENDING or NONE)
   */
  INVALID_APPROVAL_DECISION("INVALID_APPROVAL_DECISION",
      "Approval status must be either APPROVED or REJECTED",
      HttpStatus.BAD_REQUEST);;

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