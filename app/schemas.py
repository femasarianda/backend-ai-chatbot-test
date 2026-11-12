"""Model request/response (Pydantic v2)."""
from __future__ import annotations

import re
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

INVOICE_NO_RE = re.compile(r"^INV-\d{4}-\d{3}$")


class PaymentConfirmationRequest(BaseModel):
    """Klaim pembayaran dari klien.

    Validasi di sini hanya soal BENTUK data. Pemeriksaan yang bergantung pada
    database (klien terdaftar, invoice milik klien, nominal) ada di
    services/payments.py.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    client_id: str = Field(min_length=1, max_length=50)
    invoice_no: str
    nominal_transfer: StrictInt = Field(gt=0, description="Integer positif (rupiah)")
    bank_tujuan: Literal["BCA", "MANDIRI", "BRI"]
    nama_rekening_pengirim: str

    @field_validator("invoice_no")
    @classmethod
    def _check_invoice_no(cls, v: str) -> str:
        v = v.upper()
        if not INVOICE_NO_RE.match(v):
            raise ValueError("format invoice_no harus INV-YYYY-NNN")
        return v

    @field_validator("bank_tujuan", mode="before")
    @classmethod
    def _upper_bank(cls, v):
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("nama_rekening_pengirim")
    @classmethod
    def _check_name(cls, v: str) -> str:
        if len(re.sub(r"\s+", "", v)) < 3:
            raise ValueError("minimal 3 karakter non-spasi")
        return v


class PaymentConfirmationOut(BaseModel):
    id: int
    status: str
    message: str


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    client_id: str = Field(min_length=1, max_length=50)
    conversation_id: Optional[str] = Field(
        default=None, min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_\-]+$"
    )
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    conversation_id: str
    client_id: str
    reply: str
    detected_intent: str
    source: Literal["rules", "llm"] = Field(
        description="'llm' jika kalimat ditulis ulang LLM, 'rules' jika jawaban deterministik"
    )


class InvoiceOut(BaseModel):
    invoice_no: str
    service_type: str
    package_name: str
    total_amount: int
    amount_paid: int
    remaining_amount: int
    payment_status: str
    expected_status: str
    is_consistent: bool
    due_date: Optional[str] = None


class BillingResponse(BaseModel):
    client_id: str
    client_name: str
    invoices: List[InvoiceOut]
    total_remaining: int


class MessageOut(BaseModel):
    turn_index: int
    sender: str
    message_text: str
    detected_intent: Optional[str] = None
    created_at: str


class ConversationOut(BaseModel):
    conversation_id: str
    client_id: str
    created_at: str
    updated_at: str
    messages: List[MessageOut]


class KnowledgeBaseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category: str = Field(min_length=1, max_length=100)
    keyword_triggers: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)


class KnowledgeBaseOut(KnowledgeBaseCreate):
    id: int
