"""Authenticate to the LegalDesk `/Web/` portal (TOTVS juriTIs).

The portal login is NOT Basic auth. It uses a client-side RSA+AES handshake
(reverse-engineered from /Web/bundles/login/js):

1. GET /Web/login -> read hidden fields: WrapperKey (AES-GCM key+nonce),
   ServerPubKey (AES-GCM-wrapped RSA public key, base64 JSON), Seed,
   __RequestVerificationToken, State.
2. AES-GCM-decrypt ServerPubKey with WrapperKey, AAD=b"LegalDesk" -> RSA pubkey
   (JWK with byte-array n/e).
3. Encrypt the RAW password bytes with RSA-OAEP/SHA-1 -> base64url -> Password.
   (The JS does _b64strToBuffer(_utf8ToBase64(pwd)) which round-trips to raw
   bytes, so the plaintext is just the utf-8 password.)
4. Generate a client RSA keypair, export public as JWK, AES-GCM-encrypt it with
   WrapperKey -> ClientPubKey.
5. POST the form. Success = 302 away from /Web/login and an authenticated cookie.

Returns a requests.Session with the authenticated cookies set.
"""
from __future__ import annotations

import base64
import html as _html
import json
import re

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = "https://legaldesk.mbclaw.com.br"


def _field(html: str, name: str) -> str | None:
    m = re.search(rf'(?:name|id)="{name}"[^>]*value="([^"]*)"', html)
    return _html.unescape(m.group(1)) if m else None


def _client_pubkey_field(key: bytes, nonce: bytes) -> str:
    ck = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pn = ck.public_key().public_numbers()

    def i2a(i: int) -> list[int]:
        return list(i.to_bytes((i.bit_length() + 7) // 8, "big"))

    cjwk = {"alg": "RSA-OAEP", "kty": "RSA", "e": i2a(pn.e), "ext": True,
            "key_ops": ["encrypt"], "n": i2a(pn.n)}
    ctk = AESGCM(key).encrypt(nonce, json.dumps(cjwk).encode(), b"LegalDesk")
    return base64.b64encode(json.dumps(
        {"CipherText": list(ctk[:-16]), "AuthenticationTag": list(ctk[-16:])}
    ).encode()).decode()


def login(user: str, password: str) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    html = s.get(f"{ROOT}/Web/login", timeout=30).text

    wk = json.loads(_field(html, "WrapperKey"))
    key, nonce = bytes(wk["Key"]), bytes(wk["Nonce"])
    sp = json.loads(base64.b64decode(_field(html, "ServerPubKey")))
    decrypted = AESGCM(key).decrypt(
        nonce, bytes(sp["CipherText"]) + bytes(sp["AuthenticationTag"]), b"LegalDesk"
    )
    jwk = json.loads(decrypted.decode("latin-1").rstrip("\x00").strip())
    n = int.from_bytes(bytes(jwk["n"]), "big")
    e = int.from_bytes(bytes(jwk["e"]), "big")
    server_pub = rsa.RSAPublicNumbers(e, n).public_key()

    enc_pwd = server_pub.encrypt(
        password.encode("utf-8"),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA1()), algorithm=hashes.SHA1(), label=None),
    )
    enc_pwd_b64url = base64.urlsafe_b64encode(enc_pwd).decode().rstrip("=")

    data = {
        "__RequestVerificationToken": _field(html, "__RequestVerificationToken"),
        "UserName": user,
        "Password": enc_pwd_b64url,
        "ReturnUrl": "",
        "State": "Login",
        "Seed": _field(html, "Seed"),
        "Sufix": "",
        "WrapperKey": _field(html, "WrapperKey"),
        "ServerPubKey": _field(html, "ServerPubKey"),
        "ClientPubKey": _client_pubkey_field(key, nonce),
        "CurrentPwd": "",
    }
    s.post(f"{ROOT}/Web/login", data=data, timeout=30, allow_redirects=False)

    check = s.get(f"{ROOT}/Web/", timeout=30, allow_redirects=False)
    authed = not (check.status_code == 302 and "login" in check.headers.get("Location", "").lower())
    if not authed:
        raise RuntimeError("Web login failed (invalid credentials or handshake).")
    return s


if __name__ == "__main__":
    import sys
    u = sys.argv[1] if len(sys.argv) > 1 else "integracao"
    p = sys.argv[2] if len(sys.argv) > 2 else "RumoTech1!"
    sess = login(u, p)
    print("Authenticated. Cookies:", list(sess.cookies.keys()))
