package com.kltn.livability_score.property_service.model.base_format.response;

import com.kltn.livability_score.property_service.model.base_format.request.RequestPageableVO;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.math.NumberUtils;

import java.util.List;

@Setter
@Getter
public class ResponsePageableVO<T> {

  protected static final long DEFAULT_RECORDS = NumberUtils.LONG_ZERO;

  @Schema(description = "Total data in database", example = "50")
  private Long records = DEFAULT_RECORDS;

  @Schema(description = "List of data in the current page")
  private List<T> items;

  @Schema(description = "Total pages in database", example = "5")
  private Integer pages;

  @Schema(description = "Current page", example = "1")
  private Integer page;

  @Schema(description = "The first number of item in current page", example = "1")
  @JsonProperty("record_from")
  private Integer recordFrom;

  @Schema(description = "The last number of item in current page", example = "10")
  @JsonProperty("record_to")
  private Integer recordTo;

  public ResponsePageableVO(int records, List<T> items, RequestPageableVO pageable) {
    this((long) records, items, pageable);
  }

  public ResponsePageableVO(long records, List<T> items, RequestPageableVO pageable) {
    this.records = records;
    this.items = items;
    this.pages = (int) Math.ceil((double) this.records / pageable.getRpp());
    this.page = pageable.getPage();
    if (ObjectUtils.isEmpty(this.items)) {
      this.recordFrom = 1;
      this.recordTo = Math.toIntExact(this.records);
    } else {
      this.recordFrom = (this.page * pageable.getRpp()) - pageable.getRpp() + 1;
      this.recordTo = (int) (this.page.equals(this.pages) ? this.records
          : this.page * pageable.getRpp());
    }
  }
}