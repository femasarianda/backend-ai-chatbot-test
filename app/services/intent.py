"""Intent detection berbasis aturan (deterministik, tanpa LLM).

Urutan pemeriksaan disengaja: hal yang berisiko (injection, perubahan status,
klaim bayar) dicek lebih dulu agar tidak pernah jatuh ke jalur "biasa".
"""
from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    STATUS_CHANGE_REQUEST = "status_change_request"
    PAYMENT_CLAIM = "payment_claim"
    SERVICE_ACTIVATION = "service_activation"
    BILLING_INQUIRY = "billing_inquiry"
    KNOWLEDGE_QUERY = "knowledge_query"
    FALLBACK = "fallback"
    GENERAL = "general"  # sementara: belum tahu, akan dicari di knowledge base


_INJECTION = re.compile(
    r"system\s+(instruction|prompt)|instruction\s+override|\boverride\b"
    r"|abaikan\s+(semua\s+|seluruh\s+)?(aturan|instruksi|perintah)"
    r"|lupakan\s+(semua\s+)?(aturan|instruksi)"
    r"|ignore\s+(all\s+|any\s+|previous\s+)*(instructions|rules)"
    r"|developer\s+mode|jailbreak|kamu\s+sekarang\s+adalah|you\s+are\s+now"
)
_STATUS_CHANGE = re.compile(
    r"\b(ubah|ubahkan|ganti|tandai|tandain|update|set|mark|change)\b.{0,40}"
    r"\b(status|lunas|paid|tagihan|invoice)\b"
)
_PAYMENT_CLAIM = re.compile(
    r"\b(sudah|telah|udah|sdh)\s+(saya\s+)?(transfer|tf|bayar|membayar|melunasi|lunas|dibayar)\b"
)
_ACTIVATION = re.compile(
    r"aktivasi|aktifkan|diaktifkan|sambung\s*(kan)?\s+domain|go\s*live|golive"
    r"|domain\s+resmi|onlinekan|online\s+kan|naik\s+online"
)
_BILLING = re.compile(
    r"\b(sisa\s+(tagihan|pembayaran)|tagihan|invoice|tunggakan|kekurangan|status\s+pembayaran)\b"
    r"|berapa\s+yang\s+harus\s+(saya\s+)?bayar"
)


def detect_intent(message: str) -> Intent:
    text = re.sub(r"\s+", " ", message.lower())
    if _INJECTION.search(text):
        return Intent.PROMPT_INJECTION
    if _STATUS_CHANGE.search(text):
        return Intent.STATUS_CHANGE_REQUEST
    if _PAYMENT_CLAIM.search(text):
        return Intent.PAYMENT_CLAIM
    if _ACTIVATION.search(text):
        return Intent.SERVICE_ACTIVATION
    if _BILLING.search(text):
        return Intent.BILLING_INQUIRY
    return Intent.GENERAL
