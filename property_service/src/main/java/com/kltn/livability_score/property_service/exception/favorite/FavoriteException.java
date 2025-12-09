package com.kltn.livability_score.property_service.exception.favorite;


import com.kltn.livability_score.property_service.exception.type.ErrorCodeType;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;

@AllArgsConstructor
public enum FavoriteException implements ErrorCodeType {

  ALREADY_LIKED("ALREADY_LIKED", "You have already liked this property", HttpStatus.BAD_REQUEST),
  NOT_LIKED_YET("NOT_LIKED_YET", "You have not liked this property yet", HttpStatus.BAD_REQUEST);

  final String value;
  final String description;
  final HttpStatus httpStatus;

  @Override public String getValue() { return value; }
  @Override public String getDescription() { return description; }
  @Override public HttpStatus getHttpStatus() { return httpStatus; }
}