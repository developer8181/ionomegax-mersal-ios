package com.extreme.epms.olivetti;

import com.extreme.epms.ExtremeSdkServlet;

/** Olivetti Connect / INFOchip bridge. */
public final class OlivettiExtremeBridge {
    private OlivettiExtremeBridge() {}

    public static String handshake() {
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "olivetti-" + username);
    }
}
