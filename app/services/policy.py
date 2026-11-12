"""Policy check + penyusunan DRAFT jawaban dari data tepercaya (DB).

Semua keputusan bisnis dibuat di sini, di backend. Hasilnya `Decision.draft`
sudah berisi seluruh fakta (nominal, status, rekening). LLM, kalau dipakai,
hanya boleh menulis ulang gaya bahasanya (lihat chat_engine).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.services import knowledge
from app.services.billing import InvoiceView, get_billing, total_remaining
from app.services.intent import Intent

FALLBACK_REPLY = (
    "Mohon maaf kak, informasi tersebut belum tersedia di sistem kami. "
    "Tim support akan membantu memberikan informasi lebih lanjut."
)

_VERIFY_STEPS = (
    "Mohon kirimkan data berikut untuk diverifikasi: nomor invoice (format INV-YYYY-NNN), "
    "nominal transfer, bank tujuan (BCA/MANDIRI/BRI), dan nama rekening pengirim "
    "(melalui endpoint konfirmasi pembayaran atau tim support)."
)


@dataclass(frozen=True)
class Decision:
    intent: Intent
    draft: str
    # True hanya untuk jawaban yang aman ditulis ulang LLM. Penolakan,
    # klaim pembayaran, injection, dan fallback selalu teks tetap.
    allow_llm: bool = False


def rupiah(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


def _invoice_line(inv: InvoiceView) -> str:
    return (
        f"{inv.invoice_no} ({inv.package_name}): total {rupiah(inv.total_amount)}, "
        f"terbayar {rupiah(inv.amount_paid)}, sisa {rupiah(inv.remaining_amount)}, "
        f"status {inv.payment_status}"
    )


def decide(conn: sqlite3.Connection, client: sqlite3.Row, message: str, intent: Intent) -> Decision:
    name = client["client_name"]

    if intent is Intent.PROMPT_INJECTION:
        return Decision(
            intent,
            "Mohon maaf kak, permintaan tersebut tidak dapat diproses. Data tagihan dan status "
            "layanan hanya dapat diubah melalui proses verifikasi resmi di sistem kami, bukan "
            "melalui chat. " + _VERIFY_STEPS,
        )

    if intent in (Intent.STATUS_CHANGE_REQUEST, Intent.PAYMENT_CLAIM):
        _, invoices = get_billing(conn, client["client_id"])
        open_lines = [_invoice_line(i) for i in invoices if i.remaining_amount > 0]
        current = (" Saat ini tercatat: " + "; ".join(open_lines) + ".") if open_lines else ""
        return Decision(
            intent,
            f"Terima kasih kak {name}. Status pembayaran tidak dapat diubah melalui chat; "
            "pembayaran perlu diverifikasi terlebih dahulu oleh tim kami." + current + " "
            + _VERIFY_STEPS,
        )

    if intent is Intent.SERVICE_ACTIVATION:
        return _activation(conn, client)

    if intent is Intent.BILLING_INQUIRY:
        _, invoices = get_billing(conn, client["client_id"])
        if not invoices:
            return Decision(intent, f"Kak {name}, belum ada tagihan yang tercatat atas akun kakak.", True)
        if any(not i.is_consistent for i in invoices):
            return _inconsistent(intent, name)
        lines = "\n".join("- " + _invoice_line(i) for i in invoices)
        return Decision(
            intent,
            f"Berikut rincian tagihan kak {name}:\n{lines}\n"
            f"Total sisa tagihan: {rupiah(total_remaining(invoices))}.",
            True,
        )

    # GENERAL -> cari di knowledge base; tidak ketemu -> fallback (tanpa karang jawaban)
    entry = knowledge.search(conn, message)
    if entry is None:
        return Decision(Intent.FALLBACK, FALLBACK_REPLY)
    return Decision(Intent.KNOWLEDGE_QUERY, f"{entry['title']}\n{entry['content']}", True)


def _inconsistent(intent: Intent, name: str) -> Decision:
    return Decision(
        intent,
        f"Mohon maaf kak {name}, data tagihan kakak sedang perlu dicek ulang oleh tim kami "
        "sehingga belum dapat kami proses. Tim support akan segera membantu.",
    )


def _activation(conn: sqlite3.Connection, client: sqlite3.Row) -> Decision:
    intent = Intent.SERVICE_ACTIVATION
    name = client["client_name"]
    _, invoices = get_billing(conn, client["client_id"])

    if not invoices or any(not i.is_consistent for i in invoices):
        return _inconsistent(intent, name)

    unpaid = [i for i in invoices if i.remaining_amount > 0]
    if unpaid:
        lines = "\n".join("- " + _invoice_line(i) for i in unpaid)
        return Decision(
            intent,
            f"Mohon maaf kak {name}, aktivasi domain belum dapat diproses karena tagihan berikut "
            f"belum lunas:\n{lines}\nTotal sisa tagihan: {rupiah(total_remaining(invoices))}. "
            "Aktivasi dapat diproses setelah pelunasan terverifikasi.",
            True,
        )
    return Decision(
        intent,
        f"Terima kasih kak {name}. Seluruh tagihan kakak sudah lunas, sehingga permintaan aktivasi "
        "domain akan kami teruskan ke tim terkait.",
        True,
    )
