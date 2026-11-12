"""Konfirmasi pembayaran: validasi berbasis database di service layer.

Alur ini TIDAK mengubah invoice saat klien melapor. Laporan hanya dicatat
sebagai `pending`; invoice baru berubah lewat `review_confirmation`, yang
hanya dipanggil dari endpoint admin berotorisasi.
"""
from __future__ import annotations

import sqlite3

from app import repositories as repo
from app.database import transaction
from app.errors import (
    ClientNotFound,
    Conflict,
    InconsistentInvoice,
    InvoiceAlreadyPaid,
    InvoiceNotFound,
    NominalMismatch,
)
from app.schemas import PaymentConfirmationRequest
from app.services.billing import InvoiceView, expected_status


def submit_confirmation(conn: sqlite3.Connection, req: PaymentConfirmationRequest) -> int:
    if repo.get_client(conn, req.client_id) is None:
        raise ClientNotFound()

    row = repo.get_invoice(conn, req.invoice_no)
    # Invoice milik klien lain diperlakukan sama dengan "tidak ada" (tidak bocor).
    if row is None or row["client_id"] != req.client_id:
        raise InvoiceNotFound()

    invoice = InvoiceView.from_row(row)
    if not invoice.is_consistent:
        raise InconsistentInvoice()
    if invoice.remaining_amount == 0:
        raise InvoiceAlreadyPaid()
    if req.nominal_transfer > invoice.remaining_amount:
        raise NominalMismatch(
            f"Nominal transfer melebihi sisa tagihan ({invoice.remaining_amount})."
        )

    return repo.insert_confirmation(
        conn,
        req.client_id,
        req.invoice_no,
        req.nominal_transfer,
        req.bank_tujuan,
        req.nama_rekening_pengirim,
    )


def review_confirmation(conn: sqlite3.Connection, confirmation_id: int, approve: bool) -> sqlite3.Row:
    """Dipanggil HANYA oleh admin. Satu-satunya jalur yang mengubah pembayaran."""
    with transaction(conn):
        conf = repo.get_confirmation(conn, confirmation_id)
        if conf is None:
            raise Conflict("Konfirmasi pembayaran tidak ditemukan.")
        if conf["status"] != "pending":
            raise Conflict("Konfirmasi ini sudah diproses.")

        if approve:
            inv = repo.get_invoice(conn, conf["invoice_no"])
            new_paid = inv["amount_paid"] + conf["nominal_transfer"]
            if new_paid > inv["total_amount"]:
                raise NominalMismatch("Total pembayaran akan melebihi total tagihan.")
            conn.execute(
                "UPDATE invoices SET amount_paid = ?, payment_status = ? WHERE invoice_no = ?",
                (new_paid, expected_status(inv["total_amount"], new_paid), inv["invoice_no"]),
            )
        conn.execute(
            "UPDATE payment_confirmations SET status = ?, reviewed_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            ("approved" if approve else "rejected", confirmation_id),
        )
    return repo.get_confirmation(conn, confirmation_id)
