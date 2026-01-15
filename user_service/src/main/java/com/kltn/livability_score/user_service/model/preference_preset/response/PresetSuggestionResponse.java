package com.kltn.livability_score.user_service.model.preference_preset.response;


import java.math.BigDecimal;
import java.math.RoundingMode;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
public class PresetSuggestionResponse {

  private String sourcePresetName;
  private Long totalAdaptations; // Số lượng người dùng đã custom dựa trên preset này

  // Giá trị trung bình gợi ý
  private BigDecimal avgSafety;
  private BigDecimal avgEducation;
  private BigDecimal avgShopping;
  private BigDecimal avgTransportation;
  private BigDecimal avgEnvironment;
  private BigDecimal avgEntertainment;
  private BigDecimal avgHealthcare;

  // Constructor dùng cho JPQL Query
  public PresetSuggestionResponse(String sourcePresetName, Long totalAdaptations,
      Double avgSafety, Double avgEducation, Double avgShopping,
      Double avgTransportation, Double avgEnvironment,
      Double avgEntertainment, Double avgHealthcare) {
    this.sourcePresetName = sourcePresetName;
    this.totalAdaptations = totalAdaptations;
    this.avgSafety = toBigDecimal(avgSafety);
    this.avgEducation = toBigDecimal(avgEducation);
    this.avgShopping = toBigDecimal(avgShopping);
    this.avgTransportation = toBigDecimal(avgTransportation);
    this.avgEnvironment = toBigDecimal(avgEnvironment);
    this.avgEntertainment = toBigDecimal(avgEntertainment);
    this.avgHealthcare = toBigDecimal(avgHealthcare);
  }

  private BigDecimal toBigDecimal(Double value) {
    if (value == null) {
      return BigDecimal.ZERO;
    }
    return BigDecimal.valueOf(value).setScale(2, RoundingMode.HALF_UP);
  }
}