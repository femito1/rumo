# backend/app/auth/provisioning.py
"""Temporary passwords for newly provisioned users.

There is no mail delivery in this product, so a created account's password is
generated here and shown ONCE in the UI to whoever created it (RUMO, or a client's
Gestor), who passes it on. The user must change it on first login
(``User.must_change_password``), so this value is short-lived — but it is a real
credential in the meantime, hence ``secrets`` rather than ``random``.
"""
from __future__ import annotations

import secrets

#: Deliberately excludes 0/O and 1/l/I. The password gets transcribed by a human —
#: copied out of the UI, pasted into a chat, sometimes read over a call — and a
#: mistyped ambiguous character is indistinguishable from a wrong password.
TEMP_PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"

_GROUP_LEN = 4
_GROUPS = 4


def generate_temp_password() -> str:
    """A 16-character password in four hyphen-separated groups (``K7mq-2xPp-…``).

    16 draws from a 56-character alphabet is ~93 bits — far beyond what a
    change-on-first-login credential needs, and the grouping keeps it legible.
    """
    groups = [
        "".join(secrets.choice(TEMP_PASSWORD_ALPHABET) for _ in range(_GROUP_LEN))
        for _ in range(_GROUPS)
    ]
    return "-".join(groups)
