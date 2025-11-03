package com.kltn.livability_score.user_service.model.user.request;


import com.kltn.livability_score.user_service.enums.SellerApprovalStatus;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class AdminApproveSellerRequest {

  /**
   * The admin's decision. Must be APPROVED or REJECTED.
   */
  @NotNull
  private SellerApprovalStatus status;

  private String rejectReason;
}