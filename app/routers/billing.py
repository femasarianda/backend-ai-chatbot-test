import sqlite3

from fastapi import APIRouter, Depends

from app.deps import get_db, require_admin
from app.errors import AppError
from app.schemas import BillingResponse, InvoiceOut, PaymentConfirmationOut, PaymentConfirmationRequest
from app.services import billing, payments

router = APIRouter(tags=["billing"])


@router.get("/billing/{client_id}", response_model=BillingResponse)
def get_billing(client_id: str, conn: sqlite3.Connection = Depends(get_db)):
    client, invoices = billing.get_billing(conn, client_id)
    return BillingResponse(
        client_id=client["client_id"],
        client_name=client["client_name"],
        invoices=[
            InvoiceOut(**{k: getattr(i, k) for k in InvoiceOut.model_fields}) for i in invoices
        ],
        total_remaining=billing.total_remaining(invoices),
    )


@router.post("/payments/confirmations", response_model=PaymentConfirmationOut, status_code=201)
def submit_payment_confirmation(
    body: PaymentConfirmationRequest, conn: sqlite3.Connection = Depends(get_db)
):
    """Catat klaim pembayaran (status pending). Tidak mengubah invoice."""
    conf_id = payments.submit_confirmation(conn, body)
    return PaymentConfirmationOut(
        id=conf_id,
        status="pending",
        message="Konfirmasi diterima dan menunggu verifikasi tim kami. Status tagihan belum berubah.",
    )


@router.post(
    "/admin/payment-confirmations/{confirmation_id}/{decision}",
    response_model=PaymentConfirmationOut,
    dependencies=[Depends(require_admin)],
    tags=["admin"],
)
def review_payment(confirmation_id: int, decision: str, conn: sqlite3.Connection = Depends(get_db)):
    """Admin: `approve` atau `reject`. Satu-satunya jalur yang mengubah status pembayaran."""
    if decision not in ("approve", "reject"):
        raise AppError("decision harus 'approve' atau 'reject'.")
    row = payments.review_confirmation(conn, confirmation_id, approve=decision == "approve")
    return PaymentConfirmationOut(id=row["id"], status=row["status"], message="Konfirmasi diproses.")
