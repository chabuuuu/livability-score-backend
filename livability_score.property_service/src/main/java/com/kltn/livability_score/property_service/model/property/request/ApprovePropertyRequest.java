package com.kltn.livability_score.property_service.model.property.request;

import com.kltn.livability_score.property_service.enums.PropertyApprovalStatus;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class ApprovePropertyRequest {

  @NotNull
  private PropertyApprovalStatus approvalStatus;
}