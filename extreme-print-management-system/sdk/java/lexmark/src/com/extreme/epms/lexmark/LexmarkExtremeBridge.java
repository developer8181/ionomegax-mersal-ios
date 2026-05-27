package com.extreme.epms.lexmark;

import com.extreme.epms.ExtremeSdkServlet;

/** Lexmark eSF bridge. */
public final class LexmarkExtremeBridge {
    private LexmarkExtremeBridge() {}

    public static String handshake() {
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "lexmark-" + username);
    }
}
