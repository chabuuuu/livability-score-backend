package com.kltn.livability_score.property_service.configurations;


import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


// Import JtsModule từ thư viện N52
import org.n52.jackson.datatype.jts.JtsModule;

@Configuration
public class JacksonConfig {

  /**
   * Đăng ký JtsModule (từ org.n52)
   * để Jackson có thể (de)serialize các kiểu JTS Geometry.
   */
  @Bean
  public JtsModule jtsModule() {
    return new JtsModule();
  }
}