package com.kltn.livability_score.property_service.scheduler;

import com.kltn.livability_score.property_service.repository.PropertyRepository;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
@RequiredArgsConstructor
@Slf4j
public class ViewCountSyncJob {

  private final StringRedisTemplate redisTemplate;
  private final PropertyRepository propertyRepository;

  // Chạy mỗi 5 phút
  @Scheduled(fixedDelay = 300000)
  @Transactional
  public void syncViewsToDatabase() {
    // 1. Lấy danh sách các ID có thay đổi view
    Set<String> changedIds = redisTemplate.opsForSet().members("property:changed_views");

    if (changedIds == null || changedIds.isEmpty()) return;

    for (String idStr : changedIds) {
      Long propId = Long.valueOf(idStr);
      String key = "property:view_count:" + propId;

      // Lấy giá trị view hiện tại trong cache
      String viewCountStr = redisTemplate.opsForValue().get(key);
      if (viewCountStr != null) {
        Long viewsToAdd = Long.valueOf(viewCountStr);

        // Cập nhật vào DB (Cộng dồn số view trong cache vào DB)
        // Lưu ý: Logic này cần cẩn thận.
        // Cách an toàn nhất: Update viewCount = viewCount + :viewsToAdd
        propertyRepository.incrementViewCountByAmount(propId, viewsToAdd);

        // Xóa hoặc reset giá trị trong Redis sau khi sync thành công
        redisTemplate.delete(key);
        redisTemplate.opsForSet().remove("property:changed_views", idStr);
      }
    }
  }
}