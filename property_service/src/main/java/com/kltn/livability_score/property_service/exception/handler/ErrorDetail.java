package com.kltn.livability_score.property_service.exception.handler;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ErrorDetail {
    private String code;
    private String message;
    private Object data;
}
