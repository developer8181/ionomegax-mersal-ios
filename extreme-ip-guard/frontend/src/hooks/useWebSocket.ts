import { useEffect, useRef, useCallback } from 'react';
import { useMonitoringStore, useAuthStore } from '../store';
import { createWebSocket } from '../utils/api';
import type { WSMessage } from '../types';
import toast from 'react-hot-toast';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const { token } = useAuthStore();
  const { setStats, addEvents, addThreats, setConnected } = useMonitoringStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = createWebSocket(token || undefined);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        reconnectAttempts.current = 0;
        
        // Keep-alive ping
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          } else {
            clearInterval(pingInterval);
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'connected':
              if (message.stats) {
                setStats(message.stats as any);
              }
              break;

            case 'monitoring_update':
              if (message.stats) {
                setStats(message.stats as any);
              }
              if (message.events && message.events.length > 0) {
                addEvents(message.events);
              }
              if (message.threats && message.threats.length > 0) {
                addThreats(message.threats as any);
                
                // Show toast for critical threats
                message.threats.forEach((threat) => {
                  if (threat.threat_level === 'critical') {
                    toast.error(
                      `CRITICAL THREAT: ${threat.source_ip} - ${threat.threat_categories?.join(', ')}`,
                      { duration: 5000, id: threat.source_ip }
                    );
                  }
                });
              }
              if (message.recent_threats) {
                // Update stored threats with fresh data
                addThreats(message.recent_threats as any);
              }
              break;

            case 'pong':
              break;
          }
        } catch (e) {
          // Ignore parse errors for non-JSON messages
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;

        // Exponential backoff reconnect
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;

        reconnectRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch (e) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current++;
      reconnectRef.current = setTimeout(connect, delay);
    }
  }, [token, setStats, addEvents, addThreats, setConnected]);

  const disconnect = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, [setConnected]);

  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [token]);

  return { connect, disconnect };
}
