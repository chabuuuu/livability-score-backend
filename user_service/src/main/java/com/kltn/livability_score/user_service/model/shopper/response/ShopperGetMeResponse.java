package com.kltn.livability_score.user_service.model.shopper.response;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class ShopperGetMeResponse {

  private String username;

  private String fullname;

  private String profilePicture;

  private String email;

  private String phoneNumber;

  private String address;

}
