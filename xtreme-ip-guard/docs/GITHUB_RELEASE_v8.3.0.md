# Mersal v8.3.0 — Agent eBPF EDR

## What's new

- **eBPF EDR in endpoint agent** — kernel telemetry on every heartbeat
- Detects suspicious BPF program names, unprivileged kernel hooks, program/map storms
- Linux agent sends `ebpf_edr` + `edr_detections` to Command Center
- Server ingests into EDR dashboard automatically

## Requirements (Linux agent host)

```bash
sudo apt install linux-tools-common bpftool   # Debian/Ubuntu
```

## Agent config

Uses existing `agent_api_key` from `provision-organization.sh`.

## Upgrade from v8.2

```bash
git pull
pip install -r requirements.txt
python3 -m xig
# restart agents on endpoints
```

© Ionomegax Mersal v8.3.0
