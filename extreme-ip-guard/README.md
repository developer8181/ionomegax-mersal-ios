# Extreme IP Guard (XIPGuard)

**Next-Generation IP Security & Threat Intelligence Platform**

> Codename: *Sentinel* | Version 1.0.0

---

## Overview

Extreme IP Guard is a comprehensive, real-time IP security monitoring and threat intelligence platform built with modern async Python. It provides enterprise-grade network protection through multi-layered threat analysis, automated response, and a futuristic command center dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Command Center UI                   │
│         (Real-time Dashboard + WebSocket)            │
├─────────────────────────────────────────────────────┤
│                   REST API Layer                     │
│              (FastAPI + JWT Auth)                    │
├────────┬────────┬────────┬────────┬────────┬────────┤
│ Threat │  DDoS  │  Rate  │  Port  │ Brute  │Anomaly │
│ Engine │Detector│Limiter │ Scan   │ Force  │Detect  │
│        │        │        │Detector│Detector│        │
├────────┴────────┴────────┴────────┴────────┴────────┤
│              Rules Engine + Geo Intelligence          │
├─────────────────────────────────────────────────────┤
│           Async Database (SQLAlchemy + SQLite)        │
└─────────────────────────────────────────────────────┘
```

## Core Features

### Threat Intelligence Engine
- Multi-factor IP threat scoring (0-100 scale)
- Reputation scoring with time-decay
- Behavioral analysis and pattern correlation
- Automated threat classification (CRITICAL/HIGH/MEDIUM/LOW/INFO/SAFE)
- Smart recommendation generation

### Security Modules
- **DDoS Detection**: Volumetric, protocol, and application-layer attack detection with entropy analysis
- **Adaptive Rate Limiter**: Token-bucket + sliding window with threat-based dynamic limits
- **Port Scan Detector**: Sequential, random, stealth, service, and distributed scan detection
- **Brute Force Guard**: Credential stuffing, password spraying, and targeted attack detection with escalating lockouts
- **Anomaly Detector**: Statistical Z-score analysis, impossible travel detection, temporal anomaly detection

### Rules Engine
- Flexible condition-based rule evaluation
- Support for AND/OR logic across conditions
- 15+ comparison operators including IP range matching
- Priority-based rule resolution
- Automated actions: Block, Allow, Rate Limit, Quarantine, Alert, Log, Challenge, Redirect

### GeoIP Intelligence
- Country/city-level geolocation
- Geographic risk scoring by country
- Datacenter/cloud provider detection
- Geo-fencing policy enforcement
- Blocked/allowed country management

### Real-Time Dashboard
- Futuristic cybersecurity-themed UI
- Live threat event feed via WebSocket
- IP analysis and deep inspection tools
- Security module status monitoring
- Audit trail and compliance logging

## Quick Start

### Prerequisites
- Python 3.10+

### Installation

```bash
cd extreme-ip-guard
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

The platform starts on `http://localhost:8443`

### Default Credentials
- **Username**: `admin`
- **Password**: `XIPGuard@2026!`

> Change these in production via environment variables `XIPG_ADMIN_USERNAME` and `XIPG_ADMIN_PASSWORD`.

## API Documentation

Once running, access the interactive API docs:
- **Swagger UI**: `http://localhost:8443/api/docs`
- **ReDoc**: `http://localhost:8443/api/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/login` | POST | Authenticate and get JWT token |
| `/api/v1/dashboard/stats` | GET | Dashboard statistics |
| `/api/v1/ips` | GET | List tracked IPs |
| `/api/v1/ips/{ip}/analyze` | GET | Deep threat analysis |
| `/api/v1/ips/{ip}/block` | POST | Block an IP |
| `/api/v1/ips/{ip}/whitelist` | POST | Whitelist an IP |
| `/api/v1/ips/bulk-action` | POST | Bulk IP operations |
| `/api/v1/events` | GET | List threat events |
| `/api/v1/events/simulate` | POST | Simulate threat events |
| `/api/v1/rules` | GET/POST | Manage security rules |
| `/api/v1/security/ddos` | GET | DDoS detection status |
| `/api/v1/security/port-scans` | GET | Port scan detections |
| `/api/v1/security/brute-force` | GET | Brute force status |
| `/api/v1/security/anomalies` | GET | Anomaly detections |
| `/api/v1/security/geo/{ip}` | GET | GeoIP lookup |
| `/api/v1/audit` | GET | Audit log |
| `/ws/live` | WebSocket | Real-time event feed |

## Configuration

All settings can be overridden via environment variables with the `XIPG_` prefix:

| Variable | Default | Description |
|---|---|---|
| `XIPG_PORT` | 8443 | Server port |
| `XIPG_SECRET_KEY` | (built-in) | JWT secret key |
| `XIPG_THREAT_SCORE_THRESHOLD` | 70.0 | Alert threshold |
| `XIPG_AUTO_BLOCK_THRESHOLD` | 90.0 | Auto-block threshold |
| `XIPG_RATE_LIMIT_MAX_REQUESTS` | 100 | Rate limit per window |
| `XIPG_DDOS_PACKET_THRESHOLD` | 1000 | DDoS detection threshold |
| `XIPG_PORT_SCAN_THRESHOLD` | 15 | Port scan detection threshold |
| `XIPG_BRUTE_FORCE_THRESHOLD` | 10 | Brute force threshold |
| `XIPG_ANOMALY_SENSITIVITY` | 2.5 | Z-score sensitivity |

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy (async), Pydantic v2
- **Database**: SQLite (async via aiosqlite), upgradable to PostgreSQL
- **Auth**: JWT (python-jose), bcrypt password hashing
- **Real-time**: WebSocket with heartbeat and channel subscriptions
- **Frontend**: Vanilla JS with modern CSS (no framework dependencies)

## Project Structure

```
extreme-ip-guard/
├── app.py                    # Main FastAPI application
├── config/
│   └── settings.py           # Centralized configuration
├── core/
│   ├── auth.py               # JWT authentication
│   ├── database.py           # Async database engine
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   └── threat_engine.py      # Core threat intelligence engine
├── modules/
│   ├── anomaly_detector.py   # Statistical anomaly detection
│   ├── brute_force_detector.py # Brute force attack detection
│   ├── ddos_detector.py      # DDoS detection engine
│   ├── geo_intelligence.py   # GeoIP and geographic intelligence
│   ├── port_scan_detector.py # Port scan detection
│   ├── rate_limiter.py       # Adaptive rate limiting
│   └── rules_engine.py       # Security rules evaluation
├── api/
│   ├── routes.py             # REST API endpoints
│   └── websocket.py          # WebSocket real-time feed
├── templates/
│   ├── dashboard.html        # Main command center
│   └── login.html            # Authentication page
├── static/
│   ├── css/theme.css         # Futuristic cybersecurity theme
│   └── js/app.js             # Dashboard client application
├── data/                     # Database storage
├── tests/                    # Test suite
└── requirements.txt          # Python dependencies
```

## License

MIT License
