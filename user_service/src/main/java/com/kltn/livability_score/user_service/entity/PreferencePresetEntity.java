package com.kltn.livability_score.user_service.entity;


import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "preference_presets")
public class PreferencePresetEntity extends BaseEntity {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "name", nullable = false, length = 100)
  private String name;

  @Column(name = "image", columnDefinition = "text")
  private String image;

  @Column(name = "description", columnDefinition = "text")
  private String description;

  // --- Preference Weights ---
  // Use BigDecimal for SQL 'numeric' type for precision

  @Column(name = "preference_safety", precision = 5, scale = 2)
  private BigDecimal preferenceSafety;

  @Column(name = "preference_education", precision = 5, scale = 2)
  private BigDecimal preferenceEducation;

  @Column(name = "preference_shopping", precision = 5, scale = 2)
  private BigDecimal preferenceShopping;

  @Column(name = "preference_transportation", precision = 5, scale = 2)
  private BigDecimal preferenceTransportation;

  @Column(name = "preference_environment", precision = 5, scale = 2)
  private BigDecimal preferenceEnvironment;

  @Column(name = "preference_entertainment", precision = 5, scale = 2)
  private BigDecimal preferenceEntertainment;

  @Column(name = "preference_healthcare", precision = 5, scale = 2)
  private BigDecimal preferenceHealthcare;
}