package com.kltn.livability_score.property_service.specifications;

import com.kltn.livability_score.property_service.enums.SearchOperatorEnum;
import com.kltn.livability_score.property_service.model.specifications.SearchDataDto;
import com.kltn.livability_score.property_service.model.specifications.SearchFilterReq;
import jakarta.persistence.criteria.Predicate;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.data.jpa.domain.Specification;

public class SearchSpecificationBuilder<T> {

  private static Field getFieldFromEntity(String key, Class<?> entityClass) {
    try {
      return entityClass.getDeclaredField(key);
    } catch (NoSuchFieldException e) {
      return null;
    }
  }

  public Specification<T> buildSpecification(SearchDataDto searchData, Class<?> entityClass) {
    return (root, query, criteriaBuilder) -> {
      List<Predicate> predicates = new ArrayList<>();

      if (searchData.getFilters() != null) {
        for (SearchFilterReq filter : searchData.getFilters()) {
          String key = filter.getKey();
          String value = filter.getValue();
          SearchOperatorEnum operator = SearchOperatorEnum.valueOf(
              filter.getOperator().toUpperCase());

          // Convert type
          Field field = getFieldFromEntity(key, entityClass);

          Class<?> fieldType = field.getType();

          switch (operator) {
            case EQUAL:
              if (fieldType == Boolean.class || fieldType == boolean.class) {
                predicates.add(criteriaBuilder.equal(root.get(key), Boolean.parseBoolean(value)));
              } else {
                predicates.add(criteriaBuilder.equal(root.get(key), value));
              }
              break;
            case LIKE:
              predicates.add(criteriaBuilder.like(root.get(key), "%" + value + "%"));
              break;
            case RANGE: {
              String[] parts = value.split("-");
              if (parts.length == 2) {
                predicates.add(criteriaBuilder.between(
                    root.get(key), parts[0], parts[1]));
              }
              break;
            }
            case GREATER:
              predicates.add(criteriaBuilder.greaterThan(root.get(key), value));
              break;
            case GREATER_EQUAL:
              predicates.add(criteriaBuilder.greaterThanOrEqualTo(root.get(key), value));
              break;
            case LESS:
              predicates.add(criteriaBuilder.lessThan(root.get(key), value));
              break;
            case LESS_EQUAL:
              predicates.add(criteriaBuilder.lessThanOrEqualTo(root.get(key), value));
              break;
            case IN: {
              List<String> values = parseJsonArray(value);
              predicates.add(root.get(key).in(values));
              break;
            }
          }
        }
      }

      return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
    };
  }

  private List<String> parseJsonArray(String jsonArray) {
    return jsonArray.replace("[", "")
        .replace("]", "")
        .replace("\"", "")
        .split(",") != null
        ? Arrays.stream(jsonArray.replace("[", "").replace("]", "").replace("\"", "").split(","))
        .map(String::trim).collect(Collectors.toList())
        : new ArrayList<>();
  }
}
