package com.kltn.livability_score.user_service.model.user.response;

import com.kltn.livability_score.user_service.enums.SellerApprovalStatus;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class UserGetMeResponse {

  private List<String> roles;

  private SellerApprovalStatus becomeSellerApproveStatus;

  private String username;

  private String fullName;

  private String avatarUrl;

  private String email;

  private String phoneNumber;

  private String preferenceType;

  private Instant createAt;

  private Instant updateAt;

  private Long preferencePresetId;

  private BigDecimal preferenceHealthcare;

  private BigDecimal preferenceSafety;

  private BigDecimal preferenceEducation;

  private BigDecimal preferenceShopping;

  private BigDecimal preferenceTransportation;

  private BigDecimal preferenceEnvironment;

  private BigDecimal preferenceEntertainment;

  private String liveAddress;

  private Boolean verifiedPhone = false;
}
