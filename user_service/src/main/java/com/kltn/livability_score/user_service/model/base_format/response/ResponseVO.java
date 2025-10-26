package com.kltn.livability_score.user_service.model.base_format.response;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@Schema(description = "API Response", contentMediaType = "application/json")
public class ResponseVO<T> {
    @Schema(description = "Trace ID for tracking the request", example = "ABC12345678901234")
    private String traceId;

    @Schema(description = "Http status code of the response, in String type!", example = "200")
    private String status;

    @Schema(description = "Result of the response: Succeed or Failed", example = "Succeed")
    private String result;

    @Schema(description = "Error object of the response (If not have error, this will null)")
    private ResponseErrorVo error;

    @Schema(description = "Result data of the API")
    private T data;
}