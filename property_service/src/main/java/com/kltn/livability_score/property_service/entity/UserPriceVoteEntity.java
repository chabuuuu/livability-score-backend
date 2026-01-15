package com.kltn.livability_score.property_service.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;

@Entity
@Table(name = "user_price_votes")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserPriceVoteEntity extends BaseEntity{

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "property_id", nullable = false)
  private Long propertyId;

  @Column(name = "user_id")
  private Long userId;

  @Column(name = "user_price", nullable = false, precision = 19, scale = 2)
  private BigDecimal userPrice;

  @Column(name = "reason_category", length = 50)
  private String reasonCategory; // LOCATION, INTERIOR, LEGAL, OTHER

  @Column(name = "reason_text")
  private String reasonText;

}