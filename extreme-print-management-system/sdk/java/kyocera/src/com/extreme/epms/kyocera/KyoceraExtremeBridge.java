package com.extreme.epms.kyocera;

import com.extreme.epms.ExtremeSdkServlet;

/** Kyocera HyPAS bridge. */
public final class KyoceraExtremeBridge {
    private KyoceraExtremeBridge() {}

    public static String handshake() {
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "kyocera-" + username);
    }
}
