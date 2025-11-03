package com.kltn.livability_score.property_service.model.specifications;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "API Search Body", contentMediaType = "application/json")
public class SearchDataDto {

  @Schema(description = "A JSON array in the format [{ key: string, operator: string, value: string }].", nullable = true)
  private List<SearchFilterReq> filters;

  @Schema(description = "A JSON array in the format [{ key: string, type: string }].", nullable = true)
  private List<SearchSortReq> sorts;

  @Schema(description = "The limit of rows per page.\n For example, rpp = 5, page = 1 means fetching 5 rows from the first page.", example = "10", nullable = true)
  private Integer rpp;

  @Schema(description = "The page number you want to retrieve.", example = "1", nullable = true)
  private Integer page;
}