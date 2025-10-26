package com.kltn.livability_score.user_service.model.shopper.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class ShopperVerifyEmailRequest {

  /**
   * Email không được để trống và phải là email hợp lệ
   */
  @Email(message = "EMAIL_INVALID")
  @NotEmpty(message = "NOT_EMPTY_EMAIL")
  private String email;

  /**
   * Mã OTP gồm 6 ký tự
   */
  @Size(min = 6, max = 6, message = "OTP_LENGTH_INVALID")
  @NotEmpty(message = "NOT_EMPTY_OTP")
  private String otp;
}
