"""Outils de nommage (snake_case, identifiants Python valides)."""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^0-9a-zA-Z]+")
_LEADING_DIGITS = re.compile(r"^[0-9]+")


def to_snake_case(value: str) -> str:
    """Convertit une chaîne en snake_case (par ex. operationId CamelCase)."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return _NON_ALNUM.sub("_", s2).strip("_").lower()


def make_identifier(value: str, fallback: str = "tool") -> str:
    """Transforme une chaîne en identifiant Python valide, sans chiffre en tête."""
    ident = to_snake_case(value) or fallback
    if _LEADING_DIGITS.match(ident):
        ident = f"{fallback}_{ident}"
    return ident or fallback


def ensure_unique_name(name: str, existing: set[str]) -> str:
    """Garantit l'unicité d'un nom en suffixant _2, _3... si nécessaire."""
    candidate = name
    counter = 2
    while candidate in existing:
        candidate = f"{name}_{counter}"
        counter += 1
    return candidate
