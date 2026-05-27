"""Reference endpoint agent for Extreme IP Guard.

The production agent is expected to be written in Rust or Go with sensor
modules wired to OS primitives (eBPF, ETW, Endpoint Security framework on
macOS, …). This package is a pure-Python skeleton used to validate the
control-plane contract end to end.
"""
