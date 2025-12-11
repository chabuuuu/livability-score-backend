package com.kltn.livability_score.user_service.model.user.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class UserChangePasswordRequest {

  @NotBlank(message = "Old password is required")
  private String oldPassword;

  /**
   * Phải có ít nhất 8 ký tự, tối đa 30 ký tự Phải có ít nhất 1 chữ số (\d) Phải có ít nhất 1 chữ in
   * hoa ([A-Z]) Không được chứa dấu xuống dòng (\n hoặc \r)
   */
  @NotEmpty(message = "NOT_EMPTY_PASSWORD")
  @Size(min = 8, max = 30, message = "PASSWORD_LENGTH_INVALID")
  @Pattern(regexp = "^(?=.*[A-Z])(?=.*\\d)[^\\n\\r]*$", message = "PASSWORD_INVALID_RULE")
  private String newPassword;
}
