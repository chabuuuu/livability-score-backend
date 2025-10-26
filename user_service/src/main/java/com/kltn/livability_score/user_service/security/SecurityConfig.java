package com.kltn.livability_score.user_service.security;

import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authorization.AuthorizationDecision;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.session.SessionManagementFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import java.util.Arrays;
import java.util.List;

@Slf4j
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {
    private static final List<String> ACTUATOR_LOG_WHITELISTED_IPS = Arrays.asList(
            "172.10.0.11", "0:0:0:0:0:0:0:1", "127.0.0.1", "172.19.0.7"); // Prometheus ip, localhost

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http,
            LazySecurityContextProviderFilter lazySecurityContextProviderFilter) throws Exception {

        http
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                .csrf(csrf -> csrf.disable())
                .sessionManagement(se -> se.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(a -> {
                    /**
                     * Just allow actuator endpoints to be accessed by whitelisted IPs (the
                     * prometheus on localhost)
                     */
                    a.requestMatchers("/actuator/**").access((authentication, context) -> {
                        HttpServletRequest request = context.getRequest();
                        String remoteAddr = request.getRemoteAddr();
                        System.out.println("Remote log address: " + remoteAddr);
                        if (ACTUATOR_LOG_WHITELISTED_IPS.contains(remoteAddr)) {
                            return new AuthorizationDecision(true);
                        } else {
                            return new AuthorizationDecision(false);
                        }
                    });
                    a.anyRequest().permitAll();
                })
                .addFilterAfter(lazySecurityContextProviderFilter, SessionManagementFilter.class);

        return http.build();
    }

    @Bean
    CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(Arrays.asList("*"));
        configuration.setAllowedMethods(Arrays.asList("*"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

}