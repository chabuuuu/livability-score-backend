package com.kltn.livability_score.user_service.model.user.response;


import com.kltn.livability_score.user_service.enums.SellerApprovalStatus;
import java.math.BigDecimal;
import java.time.Instant;
import lombok.Data;

@Data
public class UserProfileResponse {

  private Long id; // Chính là userId
  private String fullName;
  private String phoneNumber;
  private String avatarUrl;
  private String liveAddress;
  private String preferenceType;
  private Instant updateAt;

  // Các trọng số
  private BigDecimal preferenceSafety;
  private BigDecimal preferenceEducation;
  private BigDecimal preferenceShopping;
  private BigDecimal preferenceTransportation;
  private BigDecimal preferenceEnvironment;
  private BigDecimal preferenceEntertainment;
  private BigDecimal preferenceHealthcare;

  private SellerApprovalStatus becomeSellerApproveStatus;

  // Email/Username (Lấy từ UserEntity liên quan nếu cần)
  // private String username;
}