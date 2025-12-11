package com.kltn.livability_score.user_service.model.user.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

@Data
public class UserVerifyPhoneRequest {

  @NotEmpty
  @Schema(description = "The raw format phone number", example = "0912345678")
  private String phoneNumber;

  @NotEmpty
  private String otp;

}
