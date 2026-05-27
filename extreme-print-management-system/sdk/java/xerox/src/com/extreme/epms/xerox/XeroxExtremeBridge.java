package com.extreme.epms.xerox;

import com.extreme.epms.ExtremeSdkServlet;

/** Xerox EIP bridge. */
public final class XeroxExtremeBridge {
    private XeroxExtremeBridge() {}

    public static String handshake() {
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "xerox-" + username);
    }
}
