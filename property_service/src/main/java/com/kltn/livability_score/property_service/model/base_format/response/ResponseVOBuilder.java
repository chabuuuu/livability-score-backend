package com.kltn.livability_score.property_service.model.base_format.response;

import org.springframework.http.HttpStatus;

import java.util.Objects;

public class ResponseVOBuilder {
    private final ResponseVO responseVO = new ResponseVO();

    private ResponseVOBuilder result(String result) {
        responseVO.setResult(result);
        return this;
    }

    private ResponseVOBuilder status(String status) {
        responseVO.setStatus(status);
        return this;
    }

    public ResponseVOBuilder success() {
        return new ResponseVOBuilder().result("Succeed").status("200");
    }

    public ResponseVOBuilder fail() {
        return new ResponseVOBuilder().result("Failed").status("500");
    }

    public ResponseVOBuilder error(ResponseErrorVo error, String status) {
        responseVO.setError(error);
        responseVO.setResult("Failed");
        responseVO.setStatus(Objects.requireNonNullElse(status, "500"));
        return this;
    }

    public ResponseVOBuilder addData(final Object body) {
        responseVO.setData(body);
        responseVO.setResult("Succeeded");
        responseVO.setStatus("200");
        return this;
    }

    public ResponseVOBuilder addData(final Object body, HttpStatus status) {
        responseVO.setData(body);
        responseVO.setResult("Succeeded");
        responseVO.setStatus(String.valueOf(status.value()));
        return this;
    }

    public ResponseVO build() {
        return responseVO;
    }
}