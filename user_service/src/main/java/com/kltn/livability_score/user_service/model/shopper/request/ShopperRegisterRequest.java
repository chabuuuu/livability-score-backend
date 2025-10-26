package com.kltn.livability_score.user_service.model.shopper.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class ShopperRegisterRequest {

  /**
   * Không được chứa khoảng trắng (space, tab, v.v.) Không được chứa dấu xuống dòng (\n, \r) Độ dài
   * tối thiểu 1 ký tự, tối đa 20 ký tự Chỉ được chứa chữ cái, số, dấu gạch dưới _ và dấu chấm .
   */
  @Pattern(regexp = "^[\\w.]+$", message = "USERNAME_RULE_INVALID")
  @Size(min = 1, max = 20, message = "USERNAME_LENGTH_INVALID")
  @NotEmpty(message = "NOT_EMPTY_USERNAME")
  private String username;

  /**
   * Phải có ít nhất 8 ký tự, tối đa 30 ký tự Phải có ít nhất 1 chữ số (\d) Phải có ít nhất 1 chữ in
   * hoa ([A-Z]) Không được chứa dấu xuống dòng (\n hoặc \r)
   */
  @NotEmpty(message = "NOT_EMPTY_PASSWORD")
  @Size(min = 8, max = 30, message = "PASSWORD_LENGTH_INVALID")
  @Pattern(regexp = "^(?=.*[A-Z])(?=.*\\d)[^\\n\\r]*$", message = "PASSWORD_INVALID_RULE")
  private String password;

  /**
   * Tên đầy đủ không được để trống Độ dài tối thiểu 1 ký tự, tối đa 40 ký tự
   */
  @NotEmpty(message = "NOT_EMPTY_FULLNAME")
  @Size(min = 1, max = 40, message = "FULLNAME_LENGTH_INVALID")
  private String fullname;

  /**
   * Email không được để trống và phải là email hợp lệ
   */
  @Email(message = "EMAIL_INVALID")
  @NotEmpty(message = "NOT_EMPTY_EMAIL")
  private String email;

  /**
   * Số điện thoại không được để trống Độ dài tối thiểu 1 ký tự, tối đa 30 ký tự
   */
  @NotEmpty(message = "NOT_EMPTY_PHONE_NUMBER")
  @Size(min = 9, max = 12, message = "PHONE_NUMBER_LENGTH_INVALID")
  private String phoneNumber;

  private String address;
  
}
