package com.kltn.livability_score.user_service.model.base_format.response;

import lombok.Getter;
import lombok.Setter;

public class ResponseErrorVo {
    @Getter
    @Setter()
    private String code;
    @Setter
    @Getter
    private String message;

    @Getter
    @Setter
    private Object data;

    public ResponseErrorVo(String code, String message) {
        this.code = code;
        this.message = message;
    }

    public ResponseErrorVo(String code, String message, Object data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }
}
