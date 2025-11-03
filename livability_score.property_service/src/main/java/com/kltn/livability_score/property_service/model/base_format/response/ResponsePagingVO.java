package com.kltn.livability_score.property_service.model.base_format.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "API Response (Paging)", contentMediaType = "application/json")
public class ResponsePagingVO<T> {

  @Schema(description = "Http status code of the response, in String type!", example = "200")
  private String status;

  @Schema(description = "Result of the response: Succeed or Failed", example = "Succeed")
  private String result;

  @Schema(description = "Error object of the response (If not have error, this will null)")
  private ResponseErrorVo error;

  @Schema(description = "Result data (with paging) of the API")
  private ResponsePageableVO<T> data;

  public String getResult() {
    return result;
  }

  public void setResult(String result) {
    this.result = result;
  }

  public ResponsePageableVO<T> getData() {
    return data;
  }

  public void setData(ResponsePageableVO<T> data) {
    this.data = data;
  }

  public ResponseErrorVo getError() {
    return error;
  }

  public void setError(ResponseErrorVo error) {
    this.error = error;
  }

  public String getStatus() {
    return status;
  }

  public void setStatus(String status) {
    this.status = status;
  }
}
