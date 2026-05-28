from .file_integrity import scan_critical_files
from .network_intel import collect_network_connections, suspicious_flows
from .process_intel import collect_running_processes, suspicious_process_events

__all__ = [
    "collect_running_processes",
    "suspicious_process_events",
    "collect_network_connections",
    "suspicious_flows",
    "scan_critical_files",
]

__all__ = ["collect_running_processes", "suspicious_process_events"]
