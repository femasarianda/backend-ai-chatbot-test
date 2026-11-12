-- Skema database chatbot layanan digital (SQLite).
-- Idempotent: aman dijalankan berulang kali.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clients (
    client_id       TEXT PRIMARY KEY,
    client_name     TEXT NOT NULL,
    company_name    TEXT,
    phone_number    TEXT NOT NULL,
    official_domain TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_no     TEXT PRIMARY KEY
                   CHECK (invoice_no GLOB 'INV-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9]'),
    client_id      TEXT NOT NULL REFERENCES clients(client_id) ON DELETE RESTRICT,
    service_type   TEXT NOT NULL,
    package_name   TEXT NOT NULL,
    total_amount   INTEGER NOT NULL CHECK (total_amount >= 0),
    amount_paid    INTEGER NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
    payment_status TEXT NOT NULL DEFAULT 'unpaid'
                   CHECK (payment_status IN ('unpaid', 'half_paid', 'paid')),
    due_date       DATE,
    CHECK (amount_paid <= total_amount)
);
CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id);

CREATE TABLE IF NOT EXISTS knowledge_bases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    category         TEXT NOT NULL,
    keyword_triggers TEXT NOT NULL,
    title            TEXT NOT NULL UNIQUE,
    content          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_bases(category);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    client_id       TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_conversations_client ON conversations(client_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    turn_index      INTEGER NOT NULL,
    sender          TEXT NOT NULL CHECK (sender IN ('user', 'assistant')),
    message_text    TEXT NOT NULL,
    detected_intent TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (conversation_id, turn_index)
);

-- Tabel tambahan: klaim pembayaran dari klien. Hanya MENCATAT klaim (status
-- pending); invoice baru berubah setelah diverifikasi lewat endpoint admin.
CREATE TABLE IF NOT EXISTS payment_confirmations (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id              TEXT NOT NULL REFERENCES clients(client_id),
    invoice_no             TEXT NOT NULL REFERENCES invoices(invoice_no),
    nominal_transfer       INTEGER NOT NULL CHECK (nominal_transfer > 0),
    bank_tujuan            TEXT NOT NULL CHECK (bank_tujuan IN ('BCA', 'MANDIRI', 'BRI')),
    nama_rekening_pengirim TEXT NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at            DATETIME
);
CREATE INDEX IF NOT EXISTS idx_confirmations_invoice ON payment_confirmations(invoice_no);
