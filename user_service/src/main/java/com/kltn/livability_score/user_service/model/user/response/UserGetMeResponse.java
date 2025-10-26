package com.kltn.livability_score.user_service.model.user.response;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class UserGetMeResponse {

  private String username;

  private String fullName;

  private String avatarUrl;

  private String email;

  private String phoneNumber;

  private String preferenceType;

  private Instant createAt;

  private Instant updateAt;
}
