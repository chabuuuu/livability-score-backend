package com.kltn.livability_score.property_service.exception.property;


import com.kltn.livability_score.property_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum PropertyException implements ErrorCodeType {

  PROPERTY_NOT_FOUND("PROPERTY_NOT_FOUND", "Property not found",
      HttpStatus.NOT_FOUND),

  FORBIDDEN_ACCESS("FORBIDDEN_ACCESS", "You do not have permission to modify this property",
      HttpStatus.FORBIDDEN),

  INVALID_APPROVAL_STATUS("INVALID_APPROVAL_STATUS", "Approval status cannot be PENDING",
      HttpStatus.BAD_REQUEST);

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