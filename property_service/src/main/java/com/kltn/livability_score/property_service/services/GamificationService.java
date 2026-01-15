package com.kltn.livability_score.property_service.services;

import com.kltn.livability_score.property_service.model.vote.VoteRequest;
import com.kltn.livability_score.property_service.model.vote.VoteStatsResponse;
import java.math.BigDecimal;
import org.springframework.transaction.annotation.Transactional;

public interface GamificationService {

  @Transactional
  void submitVote(VoteRequest request);

  VoteStatsResponse getVoteStats(Long propertyId, BigDecimal aiPrice);
}
