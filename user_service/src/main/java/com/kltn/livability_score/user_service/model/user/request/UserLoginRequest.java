package com.kltn.livability_score.user_service.model.user.request;

import io.swagger.v3.oas.annotations.media.Schema;
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
public class UserLoginRequest {

  /**
   * Email không được để trống và phải là email hợp lệ
   */
  @Email(message = "EMAIL_INVALID")
  @NotEmpty(message = "NOT_EMPTY_EMAIL")
  private String email;

  /**
   * Mật khẩu không được để trống Độ dài tối thiểu 3 ký tự, tối đa 30 ký tự
   */
  @NotEmpty(message = "NOT_EMPTY_PASSWORD")
  @Size(min = 3, max = 30, message = "PASSWORD_LENGTH_INVALID")
  @Schema(description = "Password", example = "hasdjJMkc??1")
  private String password;
}
