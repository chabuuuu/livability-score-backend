package com.kltn.livability_score.user_service.utils;

import com.kltn.livability_score.user_service.model.specifications.SearchDataDto;
import com.kltn.livability_score.user_service.specifications.SearchSpecificationBuilder;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;

public class SearchUtil<T> {

  /**
   * Get the specification for the search
   *
   * @param dto
   * @return
   */
  public static <T> Specification<T> getSpecification(SearchDataDto dto, Class<?> entityClass) {

    SearchSpecificationBuilder<T> builder = new SearchSpecificationBuilder<>();
    Specification<T> spec = builder.buildSpecification(dto, entityClass);

    return spec;
  }

  /**
   * Get the pageable for the search (include sort)
   *
   * @param dto
   * @return
   */
  public static <T> Pageable getPageable(SearchDataDto dto) {
    Sort sort = Sort.unsorted();
    if (dto.getSorts() != null && !dto.getSorts().isEmpty()) {
      List<Sort.Order> orders = dto.getSorts().stream()
          .map(s -> new Sort.Order(
              s.getType().equalsIgnoreCase("DESC") ? Sort.Direction.DESC : Sort.Direction.ASC,
              s.getKey()))
          .collect(Collectors.toList());
      sort = Sort.by(orders);
    }

    Pageable pageable = PageRequest.of(dto.getPage() - 1, dto.getRpp(), sort);

    return pageable;
  }
}
