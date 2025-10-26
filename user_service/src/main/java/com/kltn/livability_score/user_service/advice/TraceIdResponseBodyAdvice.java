package com.kltn.livability_score.user_service.advice;

import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;
import org.slf4j.MDC;
import org.springframework.core.MethodParameter;
import org.springframework.http.MediaType;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;

@RestControllerAdvice
public class TraceIdResponseBodyAdvice implements ResponseBodyAdvice<Object> {

  private static final String TRACE_ID_KEY = "traceId";

  @Override
  public boolean supports(MethodParameter returnType,
      Class<? extends HttpMessageConverter<?>> converterType) {
    // Trả về true để Advice này được áp dụng cho tất cả các response
    return true;
  }

  @Override
  public Object beforeBodyWrite(Object body, MethodParameter returnType,
      MediaType selectedContentType,
      Class<? extends HttpMessageConverter<?>> selectedConverterType,
      ServerHttpRequest request, ServerHttpResponse response) {

    // Lấy traceId từ MDC
    String traceId = MDC.get(TRACE_ID_KEY);

    // Nếu không có traceId hoặc body là kiểu dữ liệu không mong muốn (ví dụ: file download) thì bỏ qua
    if (traceId == null || body == null) {
      return body;
    }

    if (body instanceof ResponseVO<?>) {
      ((ResponseVO<?>) body).setTraceId(traceId);

      return body;
    }

    return body;
  }
}