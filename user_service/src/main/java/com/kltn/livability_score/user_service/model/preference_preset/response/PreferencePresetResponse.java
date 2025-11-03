package com.kltn.livability_score.user_service.model.preference_preset.response;


import java.math.BigDecimal;
import java.time.Instant;
import lombok.Data;

@Data
public class PreferencePresetResponse {

  private Long id;
  private String name;
  private String image;
  private String description;
  private Instant createAt;

  // Weights
  private BigDecimal preferenceSafety;
  private BigDecimal preferenceEducation;
  private BigDecimal preferenceShopping;
  private BigDecimal preferenceTransportation;
  private BigDecimal preferenceEnvironment;
  private BigDecimal preferenceEntertainment;
  private BigDecimal preferenceHealthcare;
}