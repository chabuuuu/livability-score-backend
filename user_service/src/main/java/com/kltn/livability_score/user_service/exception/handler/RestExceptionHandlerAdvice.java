package com.kltn.livability_score.user_service.exception.handler;

import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVOBuilder;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseErrorVo;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;

import java.util.List;

@RestControllerAdvice
@Slf4j
public class RestExceptionHandlerAdvice extends ResponseEntityExceptionHandler {

        @Override
        protected ResponseEntity<Object> handleMethodArgumentNotValid(MethodArgumentNotValidException ex,
                        HttpHeaders headers, HttpStatusCode status, WebRequest request) {

                List<String> errorMessageList = ex.getBindingResult().getAllErrors().stream()
                                .map(error -> error.getDefaultMessage()).toList();

                // Trả về thông báo lỗi chi tiết
                return new ResponseEntity<>(
                                new ResponseVOBuilder().fail()
                                                .error(new ResponseErrorVo("VALIDATE_ERROR", "Validate error",
                                                                errorMessageList), "400")
                                                .build(),
                                HttpStatus.BAD_REQUEST);
        }

        @SneakyThrows
        @ExceptionHandler(Exception.class)
        public ResponseEntity<ResponseVO> responseException(Exception ex) {
                log.error("Exception {}", ex.getMessage(), ex);
                if (ex instanceof org.springframework.security.access.AccessDeniedException) {
                        return new ResponseEntity<>(new ResponseVOBuilder().fail()
                                        .error(new ResponseErrorVo("GNR_INVALID_TOKEN", ex.getLocalizedMessage()),
                                                        "403")
                                        .build(),
                                        HttpStatus.FORBIDDEN);
                }
                return new ResponseEntity<>(new ResponseVOBuilder().fail()
                                .error(new ResponseErrorVo("E0001", ex.getLocalizedMessage()),
                                                "500")
                                .build(),
                                HttpStatus.INTERNAL_SERVER_ERROR);
        }

        @ExceptionHandler(BaseError.class)
        public ResponseEntity<ResponseVO> responseBizException(BaseError ex) {
                log.error("BizException {}", ex.getMessage(), ex);
                String code = ex.getErrorDetail().getCode();
                String message = ex.getErrorDetail().getMessage();
                Object errorData = ex.getErrorDetail().getData();
                ResponseErrorVo responseErrorVo = new ResponseErrorVo(code, message);

                if (errorData != null) {
                        responseErrorVo.setData(errorData);
                }

                String status = String.valueOf(ex.getHttpStatus().value());
                return new ResponseEntity<>(new ResponseVOBuilder().fail().error(responseErrorVo, status).build(),
                                ex.getHttpStatus());
        }
}