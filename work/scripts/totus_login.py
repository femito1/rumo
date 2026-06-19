"""Authenticate to the API TOTUS dev host (desenvld.juritis.com.br).

Same TOTVS LegalDesk RSA+AES web-login handshake as web_login.py, but pointed
at the dev environment and with a configurable host/user/password so we can
probe which credential pair the supplied password belongs to.

The local CA bundle lacks the GoDaddy intermediate for *.juritis.com.br, so we
disable verification (verify=False) -- the cert itself is valid.
"""
from __future__ import annotations

import base64
import html as _html
import json
import re
import sys

import requests
import urllib3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = "https://desenvld.juritis.com.br"


def _field(html: str, name: str) -> str | None:
    m = re.search(rf'(?:name|id)="{name}"[^>]*value="([^"]*)"', html)
    if not m:
        m = re.search(rf'value="([^"]*)"[^>]*(?:name|id)="{name}"', html)
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


def login(user: str, password: str, root: str = ROOT) -> requests.Session:
    s = requests.Session()
    s.verify = False
    s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    html = s.get(f"{root}/web/login", timeout=30).text

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
    r = s.post(f"{root}/web/login", data=data, timeout=30, allow_redirects=False)

    check = s.get(f"{root}/Web", timeout=30, allow_redirects=False)
    authed = not (check.status_code in (301, 302, 303)
                  and "login" in check.headers.get("Location", "").lower())
    return s, r, authed


def _server_message(resp: requests.Response) -> str:
    txt = resp.text
    m = re.search(r'(Usu[^<"]*senha[^<"]*|inv[^<"]*lid[^<"]*|error[^<"]*|exception[^<"]*)',
                  txt, re.I)
    return (m.group(0)[:200] if m else f"[{resp.status_code}, {len(txt)} bytes]").strip()


if __name__ == "__main__":
    pw = sys.argv[1] if len(sys.argv) > 1 else "Pt9Uk3B)x9z)Dt#T:xR"
    users = sys.argv[2:] or ["integracao"]
    for u in users:
        try:
            sess, post_resp, ok = login(u, pw)
            print(f"user={u!r}  authed={ok}  post={post_resp.status_code}  "
                  f"msg={_server_message(post_resp)!r}  cookies={list(sess.cookies.keys())}")
        except Exception as exc:  # noqa: BLE001
            print(f"user={u!r}  ERROR {type(exc).__name__}: {exc}")
