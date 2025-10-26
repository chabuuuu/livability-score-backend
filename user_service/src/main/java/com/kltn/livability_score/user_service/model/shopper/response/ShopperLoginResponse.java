package com.kltn.livability_score.user_service.model.shopper.response;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class ShopperLoginResponse {

  @Schema(description = "Token of the user", example = "user_token")
  private String token;
}
