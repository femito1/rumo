# backend/tests/test_provisioning.py
"""Temporary-password generation.

There is no e-mail delivery in this project, so a new user's password is generated
here, shown ONCE to whoever created the account, and must be changed on first login.
That makes the generator security-relevant: it is the only thing standing between a
new account and anyone who can guess it.
"""
from app.auth.provisioning import TEMP_PASSWORD_ALPHABET, generate_temp_password


def test_temp_password_is_long_enough_to_survive_being_read_aloud():
    pw = generate_temp_password()
    assert len(pw) >= 12


def test_temp_passwords_differ():
    # 200 draws: a constant or a low-entropy generator shows up immediately.
    assert len({generate_temp_password() for _ in range(200)}) == 200


def test_temp_password_avoids_visually_ambiguous_characters():
    """The password is transcribed by a human (copied out of the UI, pasted into
    chat, sometimes read over a call), so 0/O and 1/l/I must not appear at all —
    a mistyped character is indistinguishable from a wrong password."""
    for banned in "0O1lI":
        assert banned not in TEMP_PASSWORD_ALPHABET
    joined = "".join(generate_temp_password() for _ in range(50))
    assert not (set(joined) & set("0O1lI"))


def test_temp_password_is_hyphen_grouped_for_legibility():
    # Groups make it readable/dictatable; the hyphens are not part of the alphabet.
    pw = generate_temp_password()
    assert "-" in pw
    assert all(c in TEMP_PASSWORD_ALPHABET or c == "-" for c in pw)
