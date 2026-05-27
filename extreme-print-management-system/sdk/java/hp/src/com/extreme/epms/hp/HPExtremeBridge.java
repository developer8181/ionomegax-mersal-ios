package com.extreme.epms.hp;

import com.extreme.epms.ExtremeSdkServlet;

/**
 * HP OXP / Workpath bridge. Link against HP OXP SDK JAR from sdk/jars/.
 */
public final class HPExtremeBridge {

    private HPExtremeBridge() {}

    public static String handshake() {
        // TODO: call com.hp.oxp.sdk.* when JAR is on classpath
        return ExtremeSdkServlet.healthJson();
    }

    public static String authenticate(String username) {
        return ExtremeSdkServlet.authJson(username, "hp-" + username);
    }
}
