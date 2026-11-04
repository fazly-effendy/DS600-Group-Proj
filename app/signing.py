"""Tamper-proof market-data payloads, so Save stores exactly what the RM saw.

Behind the load balancer, the Compare page and the Save can be answered by
different servers, each with its own 15-minute market-data cache. If Save
fetched the figures again, the saved prices could differ from the ones on
screen. So /api/compare and /api/briefing sign the exact JSON they send
(HMAC-SHA256 with SECRET_KEY, which every server shares). The page sends that
JSON and its signature back with the Save form, and any server can check that
the figures are unchanged without fetching anything.
"""
import hashlib
import hmac
import json

from flask import current_app

SIGNATURE_HEADER = "X-Nimbus-Signature"
_CONTEXT = b"nimbus-market-payload-v1\n"


def sign_text(text: str) -> str:
    key = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(key, _CONTEXT + text.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_text(text: str, signature: str) -> bool:
    if not text or not signature:
        return False
    return hmac.compare_digest(sign_text(text), signature)


def signed_json_response(payload: dict):
    """JSON response plus the signature of its exact body text.

    ensure_ascii keeps the body pure ASCII, so the browser sends back the same
    bytes; allow_nan=False refuses figures that are not valid JSON numbers.
    """
    text = json.dumps(payload, allow_nan=False, separators=(",", ":"))
    resp = current_app.response_class(text, mimetype="application/json")
    resp.headers[SIGNATURE_HEADER] = sign_text(text)
    resp.headers["Cache-Control"] = "no-store"
    return resp
