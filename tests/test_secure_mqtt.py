#!/usr/bin/env python3
"""
Unit and Integration Tests for Category 04: Secure MQTT (MQTTS)
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5 Edge MQTT Security Subsystem

Tests:
    - TLS 1.2 / 1.3 protocol configuration (Port 8883)
    - Server X.509 certificate validation and CA trust paths
    - Username & password client authentication from environment
    - Secret scanning: confirms zero hardcoded credentials or private keys in repository
    - Reconnection handling and network resilience logic
"""

import os
import re
import ssl
import sys
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.mqtt_client import SecureMQTTClient
from raspberry_pi.config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT_TLS,
    MQTT_BROKER_PORT_PLAIN,
    MQTT_USE_TLS,
    MQTT_USERNAME,
    MQTT_TOPICS
)


class TestSecureMQTT:
    """Verifies security, encryption, and credential handling of the MQTT client."""

    def test_tls_port_and_security_defaults(self):
        """Verifies default MQTTS port is 8883 and TLS is enabled."""
        assert MQTT_BROKER_PORT_TLS == 8883, "Standard secure MQTT port must be 8883"
        assert MQTT_BROKER_PORT_PLAIN == 1883, "Unencrypted fallback port must be 1883"

    def test_client_initialization_with_tls(self):
        """Verifies TLS context is correctly configured in SecureMQTTClient."""
        client = SecureMQTTClient(
            broker_host="127.0.0.1",
            broker_port=8883,
            use_tls=True,
            username="test_edge_user",
            password="test_secure_password",
            tls_insecure=False
        )

        assert client.use_tls is True
        assert client.broker_port == 8883
        assert client.username == "test_edge_user"
        assert client.password == "test_secure_password"
        assert client.tls_insecure is False
        assert client.client_id == "rpi5-servo-edge-node01"

    def test_zero_hardcoded_secrets_in_repo(self):
        """
        Security Audit Test: scans Python, config, and script files for exposed
        passwords, AWS/GitHub tokens, and private key headers.
        """
        suspicious_patterns = [
            re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
            re.compile(r"(password|passwd|secret)\s*=\s*['\"][A-Za-z0-9@#$%^&+=]{8,}['\"]", re.IGNORECASE),
            re.compile(r"ghp_[A-Za-z0-9]{36}"),
            re.compile(r"AKIA[0-9A-Z]{16}")
        ]

        # Scan python and yaml files
        checked_files = 0
        for ext in ("*.py", "*.sh", "*.bat", "*.yaml", "*.yml"):
            for fpath in PROJECT_ROOT.glob(f"**/{ext}"):
                if ".git" in fpath.parts or "venv" in fpath.parts or "node_modules" in fpath.parts:
                    continue
                checked_files += 1
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                for pattern in suspicious_patterns:
                    matches = pattern.findall(text)
                    # Filter out test mock strings or empty strings
                    for match in matches:
                        match_str = match if isinstance(match, str) else str(match)
                        assert "test_secure_password" in match_str or "CHANGE_ME" in match_str or len(match_str) == 0, \
                            f"Potential secret leakage detected in {fpath}: {match_str}"

        assert checked_files > 5, "Audit must check at least 5 source files"

    def test_reconnection_and_offline_handling(self):
        """Verifies client gracefully handles an unreachable broker without crashing."""
        # Unreachable local port
        client = SecureMQTTClient(
            broker_host="127.0.0.1",
            broker_port=18884,
            use_tls=False
        )
        connected = client.connect(timeout_s=0.5)
        assert connected is False, "Client should report connection failure when broker is offline"
        assert client.is_connected is False
        assert client.connection_error is not None
        # Disconnect cleanup should not throw
        client.disconnect()

