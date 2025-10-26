package com.kltn.livability_score.user_service.model.user.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class UserRegisterReq {
    @NotEmpty(message = "NOT_EMPTY")
    @Schema(description = "Username", example = "haphuthinh")
    private String username;

    @NotEmpty(message = "NOT_EMPTY_PASSWORD")
    @Size(min = 8, max = 30, message = "PASSWORD_LENGTH_INVALID")
    @Schema(description = "Password", example = "hasdjJMkc??1")
    @Pattern(regexp = "^(?=.*[A-Z])(?=.*\\d)[^\\n\\r]*$", message = "PASSWORD_INVALID_RULE")
    private String password;
}
