package com.kltn.livability_score.property_service.configurations;

import com.kltn.livability_score.property_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.property_service.exception.type.ErrorCodeType;
import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.examples.Example;
import io.swagger.v3.oas.models.media.Content;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.responses.ApiResponse;
import io.swagger.v3.oas.models.responses.ApiResponses;
import jakarta.validation.Constraint;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springdoc.core.customizers.OperationCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.method.HandlerMethod;

@OpenAPIDefinition(info = @Info(title = "EVC HUB API", version = "v1.0"))
@SecurityScheme(
    name = "bearerAuth",
    type = SecuritySchemeType.HTTP,
    scheme = "bearer",
    bearerFormat = "JWT"
)
@Configuration
public class SwaggerConfig {

  private List<String> extractValidationMessages(Class<?> validateSchema) {
    List<String> messages = new ArrayList<>();
    Field[] fields = validateSchema.getDeclaredFields();

    for (Field field : fields) {
      // Lấy tất cả các annotation của field
      Annotation[] annotations = field.getDeclaredAnnotations();
      for (Annotation annotation : annotations) {
        // Kiểm tra nếu annotation có được đánh dấu bằng @Constraint (từ
        // javax.validation)
        if (annotation.annotationType().isAnnotationPresent(Constraint.class)) {
          try {
            // Tìm phương thức "message" trong annotation
            Method messageMethod = annotation.annotationType().getMethod("message");
            Object messageObj = messageMethod.invoke(annotation);
            if (messageObj != null) {
              messages.add(messageObj.toString());
            }
          } catch (Exception e) {
            // Nếu không tìm thấy phương thức "message" hoặc có lỗi, bỏ qua annotation này
          }
        }
      }
    }

    return messages;
  }

  @Bean
  public OperationCustomizer customizeOperation() {
    return (Operation operation, HandlerMethod handlerMethod) -> {
      Method method = handlerMethod.getMethod();
      if (method.isAnnotationPresent(ApiErrorResponse.class)) {
        ApiErrorResponse annotation = method.getAnnotation(ApiErrorResponse.class);
        Class<? extends Enum<?>> errorEnum = annotation.errorEnum();
        Class<?> validateSchema = annotation.validateSchema();

        ApiResponses apiResponses = operation.getResponses();
        if (apiResponses == null) {
          apiResponses = new ApiResponses();
          operation.setResponses(apiResponses);
        }

        // 1. Xử lý các lỗi từ Enum
        if (errorEnum.getEnumConstants().length != 0) {
          ApiResponses finalApiResponses = apiResponses;
          Arrays.stream(errorEnum.getEnumConstants()).forEach(error -> {
            if (error instanceof ErrorCodeType errorCode) {

              // Tạo đối tượng payload cho example
              ApiExampleErrorBody errorBody = new ApiExampleErrorBody(errorCode.getValue(),
                  errorCode.getDescription());
              ApiExampleResponse responsePayload =
                  new ApiExampleResponse(errorCode.getHttpStatus().value(), "Failed", errorBody);

              addApiErrorExample(
                  finalApiResponses,
                  String.valueOf(errorCode.getHttpStatus().value()),
                  errorCode.getHttpStatus(),
                  errorCode.getValue(),
                  errorCode.getDescription(),
                  responsePayload); // Truyền vào object, không phải chuỗi JSON
            }
          });
        }

        // 2. Xử lý lỗi validation
        if (validateSchema != Void.class) {
          List<String> messages = extractValidationMessages(validateSchema);

          // Tạo đối tượng payload cho example validation
          ApiExampleErrorBody errorBody = new ApiExampleErrorBody("VALIDATION_ERROR",
              "Input validation failed", messages);
          ApiExampleResponse responsePayload = new ApiExampleResponse(400, "Failed", errorBody);

          addApiErrorExample(
              apiResponses,
              "400",
              HttpStatus.BAD_REQUEST,
              "ValidationError",
              "Lỗi xác thực dữ liệu đầu vào",
              responsePayload); // Truyền vào object
        }
      }
      return operation;
    };
  }

  /**
   * Phương thức trợ giúp để thêm một example vào một ApiResponse. Chấp nhận một Object làm giá trị
   * example thay vì String.
   */
  private void addApiErrorExample(ApiResponses apiResponses, String statusCode,
      HttpStatus httpStatus,
      String exampleName, String exampleSummary, Object exampleValue) { // Thay đổi ở đây

    ApiResponse apiResponse = apiResponses.computeIfAbsent(statusCode, k ->
        new ApiResponse()
            .description(httpStatus.getReasonPhrase())
            .content(new Content().addMediaType("application/json", new MediaType()))
    );

    Example example = new Example()
        .summary(exampleSummary)
        .value(exampleValue); // Gán trực tiếp object vào đây

    if (apiResponse.getContent() == null) {
      apiResponse.setContent(new Content().addMediaType("application/json", new MediaType()));
    }
    apiResponse.getContent().get("application/json").addExamples(exampleName, example);
  }

  @Data
  @NoArgsConstructor
  @AllArgsConstructor
  // Bỏ qua các trường null khi serialize thành JSON
  @JsonInclude(JsonInclude.Include.NON_NULL)
  static class ApiExampleErrorBody {

    private String code;
    private String message;
    private List<String> details;

    public ApiExampleErrorBody(String code, String message) {
      this.code = code;
      this.message = message;
    }
  }

  @Data
  @NoArgsConstructor
  @AllArgsConstructor
  static class ApiExampleResponse {

    private int status;
    private String result = "Failed";
    private ApiExampleErrorBody error;
  }
}