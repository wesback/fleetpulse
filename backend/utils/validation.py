"""Validation utilities for input data."""
import re
from utils.constants import (
    MAX_HOSTNAME_LENGTH,
    MAX_PACKAGE_NAME_LENGTH,
    MAX_VERSION_LENGTH,
    MAX_OS_LENGTH
)


def validate_hostname(hostname: str) -> bool:
    """Validate hostname format and length."""
    if not hostname or len(hostname) > MAX_HOSTNAME_LENGTH:
        return False
    # Basic hostname validation (alphanumeric, dots, hyphens)
    pattern = r'^[a-zA-Z0-9.-]+$'
    return bool(re.match(pattern, hostname))


def validate_package_name(name: str) -> bool:
    """Validate package name format and length."""
    if not name or len(name) > MAX_PACKAGE_NAME_LENGTH:
        return False
    # Allow alphanumeric, dots, hyphens, underscores, plus signs, colons
    pattern = r'^[a-zA-Z0-9._+-:]+$'
    return bool(re.match(pattern, name))


def validate_version(version: str) -> bool:
    """Validate version string format and length."""
    if not version or len(version) > MAX_VERSION_LENGTH:
        return False
    # Allow common version patterns
    pattern = r'^[a-zA-Z0-9._+-:~]+$'
    return bool(re.match(pattern, version))


def validate_os(os_name: str) -> bool:
    """Validate OS name format and length."""
    if not os_name or len(os_name) > MAX_OS_LENGTH:
        return False
    # Allow alphanumeric, spaces, dots, hyphens
    pattern = r'^[a-zA-Z0-9. -]+$'
    return bool(re.match(pattern, os_name))