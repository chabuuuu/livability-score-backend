package com.kltn.livability_score.user_service.model.jwt.vo;

import static lombok.AccessLevel.PRIVATE;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.ArrayList;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.experimental.FieldDefaults;
import lombok.extern.jackson.Jacksonized;
import org.springframework.security.core.GrantedAuthority;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Jacksonized
@Builder
@FieldDefaults(level = PRIVATE)
@JsonIgnoreProperties(ignoreUnknown = true)
public class JwtTokenVo {

  Long userId;
  List<String> roles;
  String deviceId;
  String ipAddress;

  public List<GrantedAuthority> getAuthorities() {
    if (roles == null) {
      return new ArrayList<>();
    }
    return roles.stream().map(s -> (GrantedAuthority) () -> s).toList();
  }
}