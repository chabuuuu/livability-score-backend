package com.kltn.livability_score.user_service.entity;

import com.kltn.livability_score.user_service.enums.SellerApprovalStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.MapsId;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "user_profiles")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class UserProfileEntity extends BaseEntity {

  @Id
  // @Id này không cần @GeneratedValue vì nó sẽ lấy từ User
  @Column(name = "user_id")
  private Long id;

  @OneToOne(fetch = FetchType.LAZY)
  @MapsId
  @JoinColumn(name = "user_id")
  private UserEntity user;

  @Enumerated(EnumType.STRING) // Lưu trữ dưới dạng String (PENDING, APPROVED...)
  @Column(name = "become_seller_approve_status")
  private SellerApprovalStatus becomeSellerApproveStatus = SellerApprovalStatus.NONE;

  @Column(name = "full_name")
  private String fullName;

  @Column(name = "phone_number", length = 20)
  private String phoneNumber;

  @Column(name = "avatar_url", columnDefinition = "text")
  private String avatarUrl;

  @Column(name = "preference_type", length = 50)
  private String preferenceType = "default"; // Gán giá trị default

  @Column(name = "preference_safety")
  private BigDecimal preferenceSafety;

  @Column(name = "preference_education")
  private BigDecimal preferenceEducation;

  @Column(name = "preference_shopping")
  private BigDecimal preferenceShopping;

  @Column(name = "preference_transportation")
  private BigDecimal preferenceTransportation;

  @Column(name = "preference_environment")
  private BigDecimal preferenceEnvironment;

  @Column(name = "preference_entertainment")
  private BigDecimal preferenceEntertainment;

  @Column(name = "preference_healthcare")
  private BigDecimal preferenceHealthcare;

  @Column(name = "live_address")
  private String liveAddress;
}