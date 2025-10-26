package com.kltn.livability_score.user_service.exception.type;

import org.springframework.http.HttpStatus;

public interface ErrorCodeType {
    String getValue();

    String getDescription();

    HttpStatus getHttpStatus();
}