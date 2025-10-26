package com.kltn.livability_score.user_service.exception;

import org.springframework.http.HttpStatus;

import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;

import lombok.AllArgsConstructor;

@AllArgsConstructor
public enum GeneralErrorCode implements ErrorCodeType {

    /**
     * Error General exception.
     */

    GNR_BUSINESS_NOT_FOUND("GNR_BUSINESS_NOT_FOUND", "Không tìm thấy thông tin đại lý", HttpStatus.NOT_FOUND),

    GNR_BUSINESS_REQUEST_LIMIT_EXCEEDED("GNR_BUSINESS_REQUEST_LIMIT_EXCEEDED",
            "Đại lý đã dùng quá request so với quy định",
            HttpStatus.TOO_MANY_REQUESTS),

    GNR_UNAUTHORIZED("GNR_UNAUTHORIZED", "Không có quyền truy cập", HttpStatus.UNAUTHORIZED),

    GNR_WEB_DOMAIN_NOT_FOUND("GNR_WEB_DOMAIN_NOT_FOUND", "Web domain not found", HttpStatus.BAD_REQUEST),

    GNR_GOOGLE_CAPTCHA_INVALID("GNR_GOOGLE_CAPCHA_INVALID", "Invalid capcha", HttpStatus.BAD_REQUEST),

    GETTOKEN_FLIGHT_FAILED("GETTOKEN_FLIGHT-FAILED", "Failed to get token from flight",
            HttpStatus.INTERNAL_SERVER_ERROR),

    E001("E001", "General exception error.", HttpStatus.INTERNAL_SERVER_ERROR);

    final String value;
    final String description;
    final HttpStatus httpStatus;

    @Override
    public String getValue() {
        return value;
    }

    @Override
    public String getDescription() {
        return description;
    }

    @Override
    public HttpStatus getHttpStatus() {
        return httpStatus;
    }

}
