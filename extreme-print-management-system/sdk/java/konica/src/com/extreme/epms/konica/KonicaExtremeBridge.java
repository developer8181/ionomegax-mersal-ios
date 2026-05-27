package com.extreme.epms.konica;

import com.extreme.epms.ExtremeSdkServlet;

/** Konica Minolta OpenAPI bridge. */
public final class KonicaExtremeBridge {
    private KonicaExtremeBridge() {}

    public static String handshake() {
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "km-" + username);
    }
}
