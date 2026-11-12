"""Business logic tagihan (fungsi murni + pembacaan data tagihan)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app import repositories as repo
from app.errors import ClientNotFound


def remaining_amount(total_amount: int, amount_paid: int) -> int:
    """Sisa tagihan = total - dibayar, tidak pernah negatif."""
    return max(total_amount - amount_paid, 0)


def expected_status(total_amount: int, amount_paid: int) -> str:
    """Status yang SEHARUSNYA berdasarkan nominal tercatat."""
    if amount_paid >= total_amount:
        return "paid"
    if amount_paid <= 0:
        return "unpaid"
    return "half_paid"


def is_status_consistent(total_amount: int, amount_paid: int, status: str) -> bool:
    return expected_status(total_amount, amount_paid) == status


def total_paid(invoices: List["InvoiceView"]) -> int:
    return sum(i.amount_paid for i in invoices)


def total_remaining(invoices: List["InvoiceView"]) -> int:
    return sum(i.remaining_amount for i in invoices)


@dataclass(frozen=True)
class InvoiceView:
    invoice_no: str
    client_id: str
    service_type: str
    package_name: str
    total_amount: int
    amount_paid: int
    remaining_amount: int
    payment_status: str
    expected_status: str
    is_consistent: bool
    due_date: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "InvoiceView":
        total, paid = row["total_amount"], row["amount_paid"]
        status = row["payment_status"]
        return cls(
            invoice_no=row["invoice_no"],
            client_id=row["client_id"],
            service_type=row["service_type"],
            package_name=row["package_name"],
            total_amount=total,
            amount_paid=paid,
            remaining_amount=remaining_amount(total, paid),
            payment_status=status,
            expected_status=expected_status(total, paid),
            is_consistent=is_status_consistent(total, paid, status),
            due_date=row["due_date"],
        )


def get_billing(conn: sqlite3.Connection, client_id: str) -> Tuple[sqlite3.Row, List[InvoiceView]]:
    client = repo.get_client(conn, client_id)
    if client is None:
        raise ClientNotFound()
    return client, [InvoiceView.from_row(r) for r in repo.list_invoices(conn, client_id)]
