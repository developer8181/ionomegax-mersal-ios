# Extreme IP Guard

**Next-Generation Cybersecurity IP Protection System**

A comprehensive, AI-powered network security platform for real-time IP monitoring, threat intelligence, intrusion detection, and automated network defense.

---

## Features

### Command Center Dashboard
- Real-time system health monitoring (CPU, memory, disk, network)
- Threat distribution visualization with interactive charts
- Top threats overview with live threat scoring
- Geographic distribution of monitored IPs
- Recent alerts feed with one-click resolution

### IP Intelligence Hub
- Full IP lifecycle management (monitor, block, whitelist, quarantine)
- Automated IP enrichment with geolocation, ASN, ISP data
- VPN/Proxy/Tor/Bot detection
- Threat scoring with multi-vector analysis
- Bulk IP operations

### Threat Detection Engine
- Behavioral pattern recognition
- Rate limiting and DDoS detection
- Port scan detection
- SQL injection and XSS pattern matching
- Known attack tool signature detection
- Anomalous traffic pattern analysis

### Firewall Engine
- Rule-based traffic filtering with priority ordering
- Actions: Block, Allow, Rate Limit, Quarantine, Challenge, Log
- CIDR-based source filtering
- Port-specific rules
- Hit counting and rule analytics
- Toggle rules on/off in real-time

### Network Monitor
- Real-time bandwidth monitoring (in/out Mbps)
- Active connection tracking with process identification
- Network anomaly detection
- System resource monitoring
- Historical bandwidth charts

### IP Threat Analyzer
- Deep IP analysis with comprehensive intelligence report
- Multi-vector threat assessment
- Anonymizer detection (VPN, Proxy, Tor, Datacenter)
- Risk scoring and abuse confidence rating
- Network classification and geolocation

### System Events & Audit Log
- Complete audit trail of security events
- Severity-based event classification
- Event source tracking

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI |
| Database | SQLite with SQLAlchemy (async) |
| Frontend | Vanilla JS with Chart.js |
| UI Theme | Custom cybersecurity dark theme |
| Monitoring | psutil for system metrics |
| Analysis | Custom threat detection engine |

---

## Quick Start

```bash
cd extreme-ip-guard

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

Open your browser at **http://localhost:8000**

---

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard` | GET | Dashboard statistics |
| `/api/v1/ips` | GET/POST | IP management |
| `/api/v1/ips/{id}/block` | POST | Block an IP |
| `/api/v1/ips/{id}/whitelist` | POST | Whitelist an IP |
| `/api/v1/analyze` | POST | Deep IP analysis |
| `/api/v1/intel/{ip}` | GET | IP intelligence lookup |
| `/api/v1/alerts` | GET | List alerts |
| `/api/v1/firewall/rules` | GET/POST | Firewall rules |
| `/api/v1/network/stats` | GET | Network statistics |
| `/api/v1/events` | GET | System events |

---

## Architecture

```
extreme-ip-guard/
├── main.py                    # Application entry point
├── config/
│   └── settings.py            # Configuration management
├── app/
│   ├── api/
│   │   └── routes.py          # REST API endpoints
│   ├── core/
│   │   ├── threat_engine.py   # AI threat detection engine
│   │   ├── ip_intelligence.py # IP enrichment service
│   │   └── network_monitor.py # Real-time network monitor
│   ├── models/
│   │   ├── database.py        # Database configuration
│   │   └── schemas.py         # SQLAlchemy models
│   ├── services/
│   │   └── ip_service.py      # Business logic layer
│   ├── static/
│   │   ├── css/extreme.css    # Cybersecurity UI theme
│   │   └── js/app.js          # Dashboard SPA engine
│   └── templates/
│       └── index.html         # Main application template
├── requirements.txt
└── ReadMe.md
```

---

## License

MIT License
