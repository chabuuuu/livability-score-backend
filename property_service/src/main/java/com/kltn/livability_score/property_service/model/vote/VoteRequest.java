package com.kltn.livability_score.property_service.model.vote;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class VoteRequest {
  private Long propertyId;
  private BigDecimal userPrice;
  private String reasonCategory;
  private String reasonText;
}