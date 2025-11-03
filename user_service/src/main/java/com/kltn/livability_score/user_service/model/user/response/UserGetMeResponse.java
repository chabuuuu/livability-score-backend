package com.kltn.livability_score.user_service.model.user.response;

import com.kltn.livability_score.user_service.enums.SellerApprovalStatus;
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

  private Float preferenceHealthcare;

  private Float preferenceSafety;

  private Float preferenceEducation;

  private Float preferenceShopping;

  private Float preferenceTransportation;

  private Float preferenceEnvironment;

  private Float preferenceEntertainment;

  private String liveAddress;
}
