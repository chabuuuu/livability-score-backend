package com.kltn.livability_score.property_service.services.impl;


import com.kltn.livability_score.property_service.entity.PropertyEntity;
import com.kltn.livability_score.property_service.entity.UserPriceVoteEntity;
import com.kltn.livability_score.property_service.model.vote.VoteRequest;
import com.kltn.livability_score.property_service.model.vote.VoteStatsResponse;
import com.kltn.livability_score.property_service.model.vote.VoteStatsResponse.VoteDistributionItem;
import com.kltn.livability_score.property_service.repository.PropertyRepository;
import com.kltn.livability_score.property_service.repository.UserPriceVoteRepository;
import com.kltn.livability_score.property_service.services.GamificationService;
import com.kltn.livability_score.property_service.utils.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Service
@RequiredArgsConstructor
public class GamificationServiceImpl implements GamificationService {

  private final UserPriceVoteRepository voteRepository;
  private final PropertyRepository propertyRepository;

  /**
   * Lưu lượt vote của người dùng
   */
  @Transactional
  @Override
  public void submitVote(VoteRequest request) {
    Long currentUserId = SecurityUtil.getSession().getUserId();

    UserPriceVoteEntity vote = UserPriceVoteEntity.builder()
        .propertyId(request.getPropertyId())
        .userId(currentUserId)
        .userPrice(request.getUserPrice())
        .reasonCategory(request.getReasonCategory())
        .reasonText(request.getReasonText())
        .build();

    voteRepository.save(vote);
  }

  /**
   * Tính toán thống kê phân phối giá (Histogram Logic)
   */
  @Override
  public VoteStatsResponse getVoteStats(Long propertyId, BigDecimal aiPrice) {
    // 1. Lấy thông tin BĐS thực tế để lấy giá niêm yết
    PropertyEntity property = propertyRepository.findById(propertyId)
        .orElseThrow(() -> new RuntimeException("Property not found"));

    BigDecimal actualPrice = property.getPrice();

    // 2. Lấy danh sách vote
    List<UserPriceVoteEntity> votes = voteRepository.findByPropertyId(propertyId);
    List<BigDecimal> prices = new ArrayList<>(votes.stream().map(UserPriceVoteEntity::getUserPrice).toList());

    // Nếu chưa có ai vote
    if (prices.isEmpty()) {
      return VoteStatsResponse.builder()
          .totalVotes(0)
          .averageUserPrice(BigDecimal.ZERO)
          .aiPrice(aiPrice)
          .actualPrice(actualPrice) // Trả về giá thực tế
          .distribution(Collections.emptyList())
          .build();
    }

    // 3. Tính toán thống kê
    BigDecimal sum = prices.stream().reduce(BigDecimal.ZERO, BigDecimal::add);
    BigDecimal average = sum.divide(BigDecimal.valueOf(prices.size()), 2, RoundingMode.HALF_UP);

    // 4. Logic chia khoảng (Binning) cho biểu đồ
    // Thêm cả AI Price và Actual Price vào tập dữ liệu tạm để tính Min/Max range bao quát hết
    List<BigDecimal> rangeReference = new ArrayList<>(prices);
    rangeReference.add(aiPrice);
    if (actualPrice != null && actualPrice.compareTo(BigDecimal.ZERO) > 0) {
      rangeReference.add(actualPrice);
    }

    BigDecimal min = Collections.min(rangeReference).multiply(new BigDecimal("0.9"));
    BigDecimal max = Collections.max(rangeReference).multiply(new BigDecimal("1.1"));

    int binCount = 5;
    BigDecimal range = max.subtract(min);
    BigDecimal step = range.divide(BigDecimal.valueOf(binCount), 2, RoundingMode.HALF_UP);

    if (step.compareTo(BigDecimal.ZERO) == 0) {
      step = new BigDecimal("100000000");
    }

    List<VoteDistributionItem> distribution = new ArrayList<>();

    for (int i = 0; i < binCount; i++) {
      BigDecimal lowerBound = min.add(step.multiply(BigDecimal.valueOf(i)));
      BigDecimal upperBound = min.add(step.multiply(BigDecimal.valueOf(i + 1)));

      int count = 0;
      for (BigDecimal p : prices) {
        boolean condition = p.compareTo(lowerBound) >= 0;
        if (i == binCount - 1) {
          condition = condition && p.compareTo(upperBound) <= 0;
        } else {
          condition = condition && p.compareTo(upperBound) < 0;
        }

        if (condition) count++;
      }

      String label = formatBillions(lowerBound) + "-" + formatBillions(upperBound) + " Tỷ";
      distribution.add(new VoteDistributionItem(label, count));
    }

    return VoteStatsResponse.builder()
        .totalVotes(votes.size())
        .averageUserPrice(average)
        .aiPrice(aiPrice)
        .actualPrice(actualPrice) // Set giá thực tế vào response
        .distribution(distribution)
        .build();
  }

  private String formatBillions(BigDecimal value) {
    if (value == null) return "0";
    BigDecimal billions = value.divide(new BigDecimal("1000000000"), 1, RoundingMode.HALF_UP);
    return billions.toString();
  }
}