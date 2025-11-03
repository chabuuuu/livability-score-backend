package com.kltn.livability_score.property_service.utils;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.SneakyThrows;

public class MappingUtil<T> {

    @SneakyThrows
    public T stringToClass(String source, Class<T> targetClass) {
        ObjectMapper responseObjectMapper = new ObjectMapper();
        responseObjectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        return responseObjectMapper.readValue((String) source, targetClass);

    }
}
