package com.kltn.livability_score.property_service.enums;

public enum SellerApprovalStatus {
  /**
   * No request made or request was rejected and reset.
   */
  NONE,
  /**
   * User has requested seller role, pending admin review.
   */
  PENDING,
  /**
   * Admin approved the request.
   */
  APPROVED,
  /**
   * Admin rejected the request.
   */
  REJECTED
}