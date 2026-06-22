from app.auth.passwords import hash_password, verify_password


def test_hash_and_verify_roundtrip():
    h = hash_password("correct horse")
    assert h != "correct horse"
    assert verify_password("correct horse", h) is True


def test_verify_rejects_wrong_password():
    h = hash_password("correct horse")
    assert verify_password("battery staple", h) is False
