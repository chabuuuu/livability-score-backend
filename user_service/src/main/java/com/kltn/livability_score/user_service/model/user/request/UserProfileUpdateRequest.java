package com.kltn.livability_score.user_service.model.user.request;


import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import lombok.Data;

@Data
public class UserProfileUpdateRequest {

  @Size(min = 2, max = 100)
  private String fullName;

  private String avatarUrl; // Thường là một URL

  @Size(max = 255)
  private String liveAddress;

  // Các trọng số. Người dùng có thể tự điều chỉnh.
  private BigDecimal preferenceSafety;
  private BigDecimal preferenceEducation;
  private BigDecimal preferenceShopping;
  private BigDecimal preferenceTransportation;
  private BigDecimal preferenceEnvironment;
  private BigDecimal preferenceEntertainment;
  private BigDecimal preferenceHealthcare;
}