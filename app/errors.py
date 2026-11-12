"""Error domain. Tiap error membawa HTTP status code dan kode yang stabil."""
from __future__ import annotations


class AppError(Exception):
    status_code = 400
    code = "bad_request"
    message = "Permintaan tidak valid."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class ClientNotFound(AppError):
    status_code = 404
    code = "client_not_found"
    message = "Klien tidak ditemukan."


class InvoiceNotFound(AppError):
    status_code = 404
    code = "invoice_not_found"
    message = "Invoice tidak ditemukan untuk klien ini."


class ConversationNotFound(AppError):
    status_code = 404
    code = "conversation_not_found"
    message = "Percakapan tidak ditemukan."


class ConversationForbidden(AppError):
    status_code = 403
    code = "conversation_forbidden"
    message = "Percakapan ini bukan milik klien tersebut."


class NominalMismatch(AppError):
    status_code = 422
    code = "nominal_mismatch"
    message = "Nominal pembayaran tidak sesuai dengan sisa tagihan."


class InconsistentInvoice(AppError):
    status_code = 409
    code = "inconsistent_invoice_status"
    message = "Status tagihan tidak konsisten dengan nominal yang tercatat."


class InvoiceAlreadyPaid(AppError):
    status_code = 409
    code = "invoice_already_paid"
    message = "Invoice sudah lunas."


class Conflict(AppError):
    status_code = 409
    code = "conflict"
    message = "Data bertentangan dengan kondisi saat ini."


class AdminDisabled(AppError):
    status_code = 503
    code = "admin_disabled"
    message = "Endpoint admin nonaktif: ADMIN_API_KEY belum dikonfigurasi."


class Unauthorized(AppError):
    status_code = 401
    code = "unauthorized"
    message = "Kunci admin tidak valid."
