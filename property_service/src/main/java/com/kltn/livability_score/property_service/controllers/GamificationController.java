package com.kltn.livability_score.property_service.controllers;

import com.kltn.livability_score.property_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.property_service.exception.favorite.FavoriteException;
import com.kltn.livability_score.property_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.property_service.model.vote.VoteRequest;
import com.kltn.livability_score.property_service.model.vote.VoteStatsResponse;
import com.kltn.livability_score.property_service.services.GamificationService;
import com.kltn.livability_score.property_service.utils.ResponseEntityGenerator;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;

@RestController
@RequestMapping("/api/v1/properties/gamification")
@RequiredArgsConstructor
public class GamificationController {

  private final GamificationService gamificationService;

  // API 1: Submit Vote
  @PostMapping("/challenge")
  @Operation(summary = "Vote the price")
  public ResponseEntity<ResponseVO<String>> submitUserVote(
      @RequestBody VoteRequest request
  ) {
    gamificationService.submitVote(request);
    return ResponseEntityGenerator.okFormat("Voted successfully");
  }

  // API 2: Get Stats
  @GetMapping("/challenge/{propertyId}/stats")
  @Operation(summary = "Get the price stats")
  public ResponseEntity<ResponseVO<VoteStatsResponse>> getVoteStats(
      @PathVariable Long propertyId,
      @RequestParam BigDecimal ai_price // Frontend truyền giá AI xuống
  ) {
    VoteStatsResponse response = gamificationService.getVoteStats(propertyId, ai_price);
    return ResponseEntityGenerator.okFormat(response);
  }
}