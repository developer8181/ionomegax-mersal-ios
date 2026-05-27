# Extreme IP Guard v2.0

> **Next-Generation AI-Powered Network Security Platform**

A production-grade network security system combining real-time monitoring, machine learning threat detection, behavioral analytics, and automated response capabilities.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     EXTREME IP GUARD v2.0                    │
├──────────────┬───────────────────────┬───────────────────────┤
│   FRONTEND   │       BACKEND API     │     ML/AI ENGINE      │
│  React+TS    │    FastAPI (Python)   │  Ensemble Detection   │
│  Tailwind    │    WebSocket/REST     │  Isolation Forest     │
│  Recharts    │    JWT Auth           │  Behavioral UEBA      │
│  Zustand     │    SQLite/Postgres    │  MITRE ATT&CK         │
└──────────────┴───────────────────────┴───────────────────────┘
```

## Key Features

### AI/ML Detection Engine
- **Isolation Forest** – Unsupervised anomaly detection, auto-initializes with synthetic baseline data
- **Behavioral Analyzer (UEBA)** – Sliding window profiles with exponential moving average baselines
- **Signature Engine** – MITRE ATT&CK mapped rule-based detection
- **Threat Intelligence** – IP reputation scoring and CTI feed integration
- **Risk Scoring** – Weighted ensemble composite scoring (signature 35%, anomaly 30%, behavior 20%, intel 15%)
- **Auto-Response (SOAR)** – Automatic IP blocking at confidence > 80% and risk > 60

### Threat Detection Capabilities
| Threat Type | Detection Method | MITRE Technique |
|---|---|---|
| Port Scanning | Signature + Behavioral | T1046 |
| Brute Force | Signature + Rate Analysis | T1110 |
| DDoS | Signature + Volume | T1498 |
| Reconnaissance | Behavioral | T1595 |
| Lateral Movement | Behavioral + Multi-dest | T1021 |
| Data Exfiltration | Signature + Payload | T1041 |
| Zero-Day / Unknown | ML Anomaly Detection | — |

### Real-Time Dashboard
- WebSocket streaming with automatic reconnection
- Live event feed with threat level color coding
- Geographic threat map with country-level intelligence
- Threat timeline charts (12H / 24H / 48H / 7D)
- AI engine performance radar chart
- MITRE ATT&CK technique mapping visualization

### Security Policies
- Priority-based rule evaluation engine
- Actions: allow / block / monitor / alert / quarantine / rate_limit
- Conditions: source IP ranges, destination ports, protocols, countries, risk scores
- Real-time toggle and management

## Quick Start

### Development (No Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Access: http://localhost:5173

### Production (Docker Compose)

```bash
docker-compose up --build
```

Access: http://localhost

### Default Credentials

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@2026!` |
| Analyst | `analyst` | `Analyst@2026!` |

## API Documentation

Interactive API docs available at: http://localhost:8000/api/docs

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Authenticate and get JWT token |
| GET | `/api/monitoring/stats` | Real-time monitoring statistics |
| WS | `/api/monitoring/ws` | WebSocket event stream |
| GET | `/api/monitoring/threats` | Recent threat events |
| POST | `/api/monitoring/block-ip/{ip}` | Block an IP address |
| GET | `/api/analytics/threat-timeline` | Historical threat data |
| GET | `/api/analytics/geo-distribution` | Geographic threat map data |
| GET | `/api/policies` | List security policies |
| POST | `/api/policies` | Create security policy |

## Technology Stack

### Backend
- **FastAPI** – High-performance async Python framework
- **SQLAlchemy 2.0** – Async ORM with SQLite (dev) / PostgreSQL (prod)
- **scikit-learn** – ML models (Isolation Forest, ensemble methods)
- **Pydantic v2** – Data validation
- **python-jose** – JWT token management
- **loguru** – Structured logging
- **WebSockets** – Real-time streaming

### Frontend
- **React 18 + TypeScript** – Component-based UI
- **Tailwind CSS** – Utility-first styling with custom cyber theme
- **Recharts** – Analytics visualization
- **Zustand** – Lightweight state management
- **framer-motion** – Smooth animations
- **lucide-react** – Icon library

### Infrastructure
- **Docker + Docker Compose** – Containerization
- **Nginx** – Reverse proxy and static serving

## Security Considerations

- All API endpoints require JWT authentication
- Passwords are bcrypt-hashed
- CORS configuration restricts origins
- Request processing time headers
- Audit logging for all admin actions
- Rate limiting ready (slowapi integration)

## Project Structure

```
extreme-ip-guard/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, security, database
│   │   ├── ml/             # AI/ML threat detection engine
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── routers/        # FastAPI route handlers
│   │   ├── services/       # Business logic services
│   │   └── main.py         # Application entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── pages/          # Page components
│   │   ├── store/          # Zustand state management
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # API client, helpers
│   └── package.json
└── docker-compose.yml
```

---

*Extreme IP Guard v2.0 — Built with advanced cybersecurity expertise*
