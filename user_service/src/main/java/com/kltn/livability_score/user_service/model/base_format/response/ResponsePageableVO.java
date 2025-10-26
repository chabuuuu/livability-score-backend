package com.kltn.livability_score.user_service.model.base_format.response;

import com.kltn.livability_score.user_service.model.base_format.request.RequestPageableVO;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.math.NumberUtils;

import java.util.List;

@Setter
@Getter
public class ResponsePageableVO {
    protected static final long DEFAULT_RECORDS = NumberUtils.LONG_ZERO;
    private Long records = DEFAULT_RECORDS;
    private List<?> items;
    private Integer pages;
    private Integer page;

    @JsonProperty("record_from")
    private Integer recordFrom;
    @JsonProperty("record_to")
    private Integer recordTo;

    public ResponsePageableVO(int records, List<?> items, RequestPageableVO pageable) {
        this((long) records, items, pageable);
    }

    public ResponsePageableVO(long records, List<?> items, RequestPageableVO pageable) {
        this.records = records;
        this.items = items;
        this.pages = (int) Math.ceil((double) this.records / pageable.getRpp());
        this.page = pageable.getPage();
        if (ObjectUtils.isEmpty(this.items)) {
            this.recordFrom = 1;
            this.recordTo = Math.toIntExact(this.records);
        } else {
            this.recordFrom = (this.page * pageable.getRpp()) - pageable.getRpp() + 1;
            this.recordTo = (int) (this.page.equals(this.pages) ? this.records : this.page * pageable.getRpp());
        }
    }
}
