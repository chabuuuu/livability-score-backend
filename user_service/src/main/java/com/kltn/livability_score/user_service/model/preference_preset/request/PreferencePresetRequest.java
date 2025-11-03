package com.kltn.livability_score.user_service.model.preference_preset.request;


import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.PositiveOrZero;
import java.math.BigDecimal;
import lombok.Data;

@Data
public class PreferencePresetRequest {

  @NotEmpty
  private String name;

  private String image;

  private String description;

  // Add validation for weights (e.g., must be between 0.00 and 5.00)
  // numeric(5, 2) can hold up to 999.99

  @PositiveOrZero
  private BigDecimal preferenceSafety;

  @PositiveOrZero
  private BigDecimal preferenceEducation;

  @PositiveOrZero
  private BigDecimal preferenceShopping;

  @PositiveOrZero
  private BigDecimal preferenceTransportation;

  @PositiveOrZero
  private BigDecimal preferenceEnvironment;

  @PositiveOrZero
  private BigDecimal preferenceEntertainment;

  @PositiveOrZero
  private BigDecimal preferenceHealthcare;
}