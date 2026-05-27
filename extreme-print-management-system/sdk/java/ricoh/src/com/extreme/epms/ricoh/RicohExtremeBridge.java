package com.extreme.epms.ricoh;

import com.extreme.epms.ExtremeSdkServlet;

/** Ricoh SmartSDK bridge. */
public final class RicohExtremeBridge {
    private RicohExtremeBridge() {}

    public static String handshake() {
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "ricoh-" + username);
    }
}
