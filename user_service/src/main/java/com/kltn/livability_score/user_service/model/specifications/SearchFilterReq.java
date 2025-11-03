package com.kltn.livability_score.user_service.model.specifications;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class SearchFilterReq {

  @Schema(description = "The key to search by. For example: title, release_date, ...")
  private String key;

  @Schema(description = """
      ### The operator is the type of query operation. It supports the following types:
      
      - `equal`: Exact match
        ```json
        [{ "key": "email", "operator": "equal", "value": "example@domain.com" }]
        ```
      
      - `like`: Partial match
        ```json
        [{ "key": "name", "operator": "like", "value": "ha phu" }]
        ```
      
      - `range`: Value in range A to B (inclusive)
        ```json
        [{ "key": "salary", "operator": "range", "value": "3000-5000" }]
        ```
      
      - `greater_equal`, `greater`, `less_equal`, `less`: Comparison operators
        ```json
        [
          { "key": "salary", "operator": "greater", "value": "3000" },
          { "key": "salary", "operator": "less_equal", "value": "5000" }
        ]
        ```
      
      - `in`: Value in a list
        ```json
        [{ "key": "role", "operator": "in", "value": "["TIEP_TAN","KHACH_HANG","KE_TOAN"]" }]
        ```
      """)
  private String operator;

  @Schema(description = "The value to search by. For example: 'ha phu', '3000-5000', ...")
  private String value;
}