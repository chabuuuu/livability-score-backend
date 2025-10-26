package com.kltn.livability_score.user_service.utils;

import com.google.gson.Gson;

public class GsonParserUtils {
    public static String parseObjectToString(Object object) {
        return new Gson().toJson(object);
    }

    public static <T> T parseStringToObject(String json, Class<T> classObject) {
        try {
            return new Gson().fromJson(json, classObject);
        } catch (Exception e) {
            return null;
        }
    }
}