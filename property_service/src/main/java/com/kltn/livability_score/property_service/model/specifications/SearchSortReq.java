package com.kltn.livability_score.property_service.model.specifications;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class SearchSortReq {

  @Schema(description = "The key to sort by. For example: title, release_date, ...")
  private String key;

  @Schema(description = "The type of sorting: ASC || DESC")
  private String type; // ASC or DESC
}