import os
from collections.abc import Mapping

import streamlit as st


def _normalize_secret_value(value: object | None) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1]:
        if normalized[0] in {"'", '"'}:
            normalized = normalized[1:-1].strip()

    if not normalized:
        return None

    return normalized


def _read_secret_path(path: tuple[str, ...]) -> str | None:
    try:
        current: object = st.secrets
    except Exception:
        return None

    for segment in path:
        if not isinstance(current, Mapping):
            return None
        try:
            current = current[segment]
        except Exception:
            return None

    return _normalize_secret_value(current)


def resolve_fmp_api_key() -> str | None:
    key_from_flat_secret = _read_secret_path(("FMP_API_KEY",))
    if key_from_flat_secret:
        return key_from_flat_secret

    key_from_nested_secret = _read_secret_path(("fmp", "api_key"))
    if key_from_nested_secret:
        return key_from_nested_secret

    return _normalize_secret_value(os.getenv("FMP_API_KEY"))
