package com.kltn.livability_score.user_service.utils;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.kltn.livability_score.user_service.model.jwt.vo.JwtForgotPasswordVo;
import com.kltn.livability_score.user_service.model.jwt.vo.JwtTokenVo;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Date;

@Slf4j
@NoArgsConstructor(access = AccessLevel.PRIVATE)
public class SecurityUtil {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String AUTHORIZATION_PREFIX = "Bearer ";
    private static final int SEVEN_DAYS = 1000 * 60 * 60 * 24 * 7;
    private static final int THIRTY_MINUTES = 1000 * 60 * 30;
    private static final int FIVE_MINUTES = 1000 * 60 * 5;

    private static final String USER_CLAIM = "user";
    private static final String ISSUER = "auth0";

    private static String SECRET_KEY = System.getenv("LOGIN_JWT_KEY");

    private static final Algorithm ALGORITHM = Algorithm.HMAC256(SECRET_KEY);

    @SneakyThrows
    public static String createRefreshToken(JwtTokenVo jwtTokenVo) {
        var builder = JWT.create();
        String tokenJson;
        try {
            tokenJson = OBJECT_MAPPER.writeValueAsString(jwtTokenVo);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
        builder.withClaim(USER_CLAIM, tokenJson);
        // Thời gian hết hạn của Refresh Token dài hơn Access Token
        return builder
                .withIssuedAt(new Date())
                .withIssuer(ISSUER)
                .withExpiresAt(new Date(System.currentTimeMillis() + SEVEN_DAYS)) // 7 ngày
                .sign(ALGORITHM);
    }

    @SneakyThrows
    public static String createToken(JwtTokenVo jwtTokenVo) {
        var builder = JWT.create();
        String tokenJson = null;
        try {
            tokenJson = OBJECT_MAPPER.writeValueAsString(jwtTokenVo);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
        builder.withClaim(USER_CLAIM, tokenJson);
        return builder
                .withIssuedAt(new Date())
                .withIssuer(ISSUER)
                .withExpiresAt(new Date(System.currentTimeMillis() + THIRTY_MINUTES)) // 30 phút
                .sign(ALGORITHM);
    }

    @SneakyThrows
    public static String createTokenForgotPassword(JwtForgotPasswordVo jwtTokenVo) {
        var builder = JWT.create();
        String tokenJson = null;
        try {
            tokenJson = OBJECT_MAPPER.writeValueAsString(jwtTokenVo);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
        builder.withClaim(USER_CLAIM, tokenJson);
        return builder
                .withIssuedAt(new Date())
                .withIssuer(ISSUER)
                .withExpiresAt(new Date(System.currentTimeMillis() + FIVE_MINUTES)) // 5 phút
                .sign(ALGORITHM);
    }

    @SneakyThrows
    public static DecodedJWT validate(String token) {
        var verifier = JWT.require(ALGORITHM)
                .withIssuer(ISSUER)
                .build();
        return verifier.verify(token);
    }

    @SneakyThrows
    public static JwtForgotPasswordVo getForgotPasswordValueObject(DecodedJWT decodedJWT) {
        var userClaim = decodedJWT.getClaims().get(USER_CLAIM).asString();
        try {
            return OBJECT_MAPPER.readValue(userClaim, JwtForgotPasswordVo.class);
        } catch (JsonProcessingException e) {
            // log error
            System.out.println("Error: " + e.getMessage());

            throw new RuntimeException(e);
        }
    }

    @SneakyThrows
    public static JwtTokenVo getValueObject(DecodedJWT decodedJWT) {
        var userClaim = decodedJWT.getClaims().get(USER_CLAIM).asString();
        try {
            return OBJECT_MAPPER.readValue(userClaim, JwtTokenVo.class);
        } catch (JsonProcessingException e) {
            // log error
            System.out.println("Error: " + e.getMessage());

            throw new RuntimeException(e);
        }
    }

    public static String getToken(HttpServletRequest req) throws AccessDeniedException {
        var token = req.getHeader(AUTHORIZATION_HEADER);
        // Check if token is null
        if (token == null) {
            throw new AccessDeniedException("Not authorized.");
        }
        // Check if token is not start with Bearer
        if (!token.startsWith(AUTHORIZATION_PREFIX)) {
            throw new AccessDeniedException("Not authorized.");
        }

        String jwtToken = token.substring(AUTHORIZATION_PREFIX.length());
        return jwtToken;
    }

    public static JwtTokenVo getSession() {
        var authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication instanceof AnonymousAuthenticationToken) {
            throw new AccessDeniedException("Not authorized.");
        }
        return (JwtTokenVo) authentication.getPrincipal();
    }
}
