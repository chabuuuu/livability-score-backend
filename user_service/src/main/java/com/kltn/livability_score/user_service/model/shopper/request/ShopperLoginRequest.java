package com.kltn.livability_score.user_service.model.shopper.request;

import io.swagger.v3.oas.annotations.media.Schema;
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
public class ShopperLoginRequest {

  @Size(max = 70, message = "USERNAME_LENGTH_INVALID")
  @NotEmpty(message = "NOT_EMPTY_USERNAME")
  @Schema(description = "Username", example = "haphuthinh")
  private String username;

  /**
   * Mật khẩu không được để trống Độ dài tối thiểu 3 ký tự, tối đa 30 ký tự
   */
  @NotEmpty(message = "NOT_EMPTY_PASSWORD")
  @Size(min = 3, max = 30, message = "PASSWORD_LENGTH_INVALID")
  @Schema(description = "Password", example = "hasdjJMkc??1")
  private String password;
}
