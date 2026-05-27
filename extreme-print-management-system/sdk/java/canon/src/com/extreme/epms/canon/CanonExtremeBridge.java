package com.extreme.epms.canon;

import com.extreme.epms.ExtremeSdkServlet;

/** Canon MEAP bridge — link against Canon MEAP SDK in sdk/jars/. */
public final class CanonExtremeBridge {

    private CanonExtremeBridge() {}

    public static String handshake() {
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "canon-" + username);
    }
}
