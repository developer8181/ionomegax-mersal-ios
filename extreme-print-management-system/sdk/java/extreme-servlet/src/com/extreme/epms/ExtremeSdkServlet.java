package com.extreme.epms;

/**
 * Universal Extreme Print servlet for embedded MFD platforms.
 * Deploy behind vendor HTTP stack (OXP, MEAP, HyPAS, etc.).
 *
 * Endpoints:
 *   GET/POST /extreme/sdk/v1/health
 *   POST     /extreme/sdk/v1/auth
 *   POST     /extreme/sdk/v1/jobs/{id}/release
 *   POST     /extreme/sdk/v1/jobs/{id}/deny
 */
public final class ExtremeSdkServlet {

    private ExtremeSdkServlet() {}

    public static String healthJson() {
        return "{\"ok\":true,\"product\":\"Extreme Print\",\"api\":\"v1\"}";
    }

    public static String authJson(String username, String sessionToken) {
        return String.format(
            "{\"ok\":true,\"username\":\"%s\",\"session_token\":\"%s\"}",
            username,
            sessionToken
        );
    }

    public static String jobActionJson(int jobId, String action) {
        return String.format("{\"ok\":true,\"job_id\":%d,\"action\":\"%s\"}", jobId, action);
    }
}
