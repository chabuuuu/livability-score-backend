package com.kltn.livability_score.user_service.utils;

import com.kltn.livability_score.user_service.annotations.EnumValidator;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

import java.util.Arrays;

public class EnumValidatorImpl implements ConstraintValidator<EnumValidator, String> {

    private Enum<?>[] enumValues;

    @Override
    public void initialize(EnumValidator annotation) {
        enumValues = annotation.enumClass().getEnumConstants();
    }

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null) {
            return true;
        }
        return Arrays.stream(enumValues).anyMatch(e -> e.name().equals(value));
    }
}