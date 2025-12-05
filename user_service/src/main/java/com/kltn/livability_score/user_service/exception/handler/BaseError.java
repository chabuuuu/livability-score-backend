package com.kltn.livability_score.user_service.exception.handler;

import com.kltn.livability_score.user_service.exception.GeneralErrorCode;
import com.kltn.livability_score.user_service.exception.type.ErrorCodeType;
import lombok.Getter;
import lombok.Setter;
import org.springframework.http.HttpStatus;

public class BaseError extends RuntimeException {

  private static final long serialVersionUID = 4127513561428645333L;

  @Getter
  private ErrorCodeType error;
  @Setter
  @Getter
  private ErrorDetail errorDetail;
  @Getter
  private String description;
  @Getter
  @Setter
  private HttpStatus httpStatus = HttpStatus.INTERNAL_SERVER_ERROR;

  public BaseError() {
    this("General exception error.");
  }

  public BaseError(String description) {
    super(description);
    error = GeneralErrorCode.E001;
    this.description = description;
  }

  public BaseError(String code, String message, HttpStatus httpStatus, Object errorData) {
    this.errorDetail = new ErrorDetail();
    this.errorDetail.setMessage(message);
    this.errorDetail.setCode(code);
    this.errorDetail.setData(errorData);
    this.httpStatus = httpStatus;
  }

  public BaseError(String code, String message, HttpStatus httpStatus) {
    this.errorDetail = new ErrorDetail();
    this.errorDetail.setMessage(message);
    this.errorDetail.setCode(code);
    this.httpStatus = httpStatus;
  }

  public BaseError(ErrorCodeType bizError, String description) {
    super(description);

    this.error = bizError;
    this.description = description;
  }

  public BaseError(ErrorCodeType generalError) {
    this.errorDetail = new ErrorDetail();
    this.errorDetail.setMessage(generalError.getDescription());
    this.errorDetail.setCode(generalError.getValue());
    this.httpStatus = generalError.getHttpStatus();
  }

}
