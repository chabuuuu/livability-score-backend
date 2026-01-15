package com.kltn.livability_score.property_service.model.vote;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

@Data
@Builder
public class VoteStatsResponse {
  private long totalVotes;
  private BigDecimal averageUserPrice;
  private BigDecimal aiPrice;
  private BigDecimal actualPrice;
  private List<VoteDistributionItem> distribution;

  @Data
  @AllArgsConstructor
  public static class VoteDistributionItem {
    private String rangeLabel; // Ví dụ: "4.5-5.0 Tỷ"
    private int count;         // Số người vote trong khoảng này
  }
}