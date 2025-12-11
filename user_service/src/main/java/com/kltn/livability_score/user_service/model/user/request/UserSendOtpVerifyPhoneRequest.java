package com.kltn.livability_score.user_service.model.user.request;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
public class UserSendOtpVerifyPhoneRequest {

  @NotEmpty
  @Pattern(regexp = "^(0|\\+84)[0-9]{9}$", message = "Invalid phone number")
  private String phoneNumber;

}
