package com.kltn.livability_score.user_service.annotations;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import com.kltn.livability_score.user_service.exception.handler.NoException;

@Target({ ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface ApiErrorResponse {
    /**
     * Error enum class of the API
     * 
     * @return
     */
    Class<? extends Enum<?>> errorEnum() default NoException.class;

    /**
     * Validate class of the API. In many cases its the request class of the API
     * 
     * @return
     */
    Class<?> validateSchema() default Void.class;
}