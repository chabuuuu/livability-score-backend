package com.kltn.livability_score.property_service.exception;

import org.springframework.http.HttpStatus;

import com.kltn.livability_score.property_service.exception.type.ErrorCodeType;

import lombok.AllArgsConstructor;

@AllArgsConstructor
public enum UserRegisterException implements ErrorCodeType {

    /**
     * Error User register exception.
     */
    USER_REGISTES_UserAlreadyExist("USER_REGISTES_UserAlreadyExist", "Người dùng đã tồn tại",
            HttpStatus.NOT_ACCEPTABLE),

    ;

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
