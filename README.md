# Backend Chatbot Layanan Digital

Backend chatbot multi-klien berbasis **FastAPI + SQLite + LLM (Google Gemini)**. Chatbot menjawab dari knowledge base, membaca data klien dan tagihan, menyimpan riwayat percakapan per klien, serta menegakkan aturan bisnis di backend, bukan di LLM.

> Soal asli ada di [`TECHNICAL_TEST.md`](TECHNICAL_TEST.md). Analisis 3 studi kasus ada di [`DEBUGGING.md`](DEBUGGING.md).

## Prinsip desain

```
User Input â†’ Intent Detection â†’ Policy Check â†’ Knowledge Retrieval â†’ Response Generation â†’ Save Conversation
              (rules)            (backend/DB)   (keyword scoring)     (LLM menulis ulang)    (SQLite)
```

- **Keputusan bisnis dan fakta (nominal, status, rekening) dibuat backend dari database**, lalu disusun menjadi *draft jawaban*.
- **LLM hanya menulis ulang gaya bahasa draft.** Hasilnya divalidasi (`is_safe_rewrite`): jika ada angka berubah, hilang, atau bertambah, draft asli yang dipakai.
- **LLM tidak dipanggil sama sekali** untuk penolakan, klaim pembayaran, prompt injection, dan fallback. Jawabannya teks tetap.
- **Provider LLM gagal** (429, timeout, error, circuit terbuka): chatbot tetap menjawab dengan draft deterministik, bukan HTTP 500.
- **Status pembayaran tidak bisa diubah lewat chat.** Klaim hanya dicatat (`pending`). Perubahan hanya lewat endpoint admin berkunci.
- **Tidak ada state global per klien.** Koneksi DB dibuat per request, dan semua query memakai `client_id` yang tervalidasi.

## Teknologi

Python 3.10+, FastAPI, Uvicorn, Pydantic v2, SQLite (`sqlite3` bawaan), `httpx` (klien Gemini REST), `python-dotenv`, Pytest.
Tidak memakai SDK LLM tambahan; Gemini dipanggil langsung lewat REST.

## Instalasi

```bash
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # Windows: copy .env.example .env
# edit .env: isi GEMINI_API_KEY (lihat di bawah)
```

**API key Gemini:** buat di <https://aistudio.google.com/apikey> (free tier) lalu isi `GEMINI_API_KEY` di `.env`. Key hanya dibaca dari environment dan `.env` sudah ada di `.gitignore`.
Tanpa key (atau `LLM_PROVIDER=mock`) aplikasi memakai **MockLLM** yang tidak butuh internet, sehingga semua fitur dan tes tetap berjalan.

## Menjalankan

```bash
python init_db.py            # opsional: DB juga dibuat otomatis saat startup
uvicorn main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- `python init_db.py --reset` menghapus dan membuat ulang database (data seed kembali ke awal).

## Menjalankan tes

```bash
pytest -q
```

33 tes: skenario TC-01 s/d TC-10, validasi, guardrail dan fallback LLM, circuit breaker, serta unit test logika tagihan. Tes memakai MockLLM dan DB sementara, jadi tidak butuh API key.

## Endpoint

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/health` | Status server, database, dan provider LLM |
| POST | `/chat` | Proses pesan. Tanpa `conversation_id` â†’ sesi baru |
| GET | `/billing/{client_id}` | Tagihan klien (nominal, sisa, status, konsistensi) |
| GET | `/conversations/{id}` | Riwayat sesi. Wajib header `X-Client-ID` |
| DELETE | `/conversations/{id}` | Hapus sesi. Wajib header `X-Client-ID` â†’ 204 |
| GET | `/knowledge-bases` | Daftar KB (filter `?category=`) |
| POST | `/knowledge-bases` | Tambah KB. **Admin**: header `X-Admin-Key` |
| POST | `/payments/confirmations` | Catat klaim pembayaran (`pending`), tidak mengubah invoice |
| POST | `/admin/payment-confirmations/{id}/approve\|reject` | **Admin**: satu-satunya jalur yang mengubah status pembayaran |

**Kode status:** `404` klien/sesi/invoice tidak ada Â· `403` sesi milik klien lain Â· `422` validasi Â· `409` konflik/invoice sudah lunas/status tidak konsisten Â· `401` kunci admin salah Â· `503` admin dinonaktifkan (`ADMIN_API_KEY` kosong). Format error: `{"error": {"code": "...", "message": "..."}}`.

Catatan `/chat`: jika `conversation_id` dikirim tetapi belum ada, sesi dibuat dengan ID itu untuk klien tersebut. Jika sudah ada dan milik klien lain â†’ `403`.

## Contoh request dan response

**Informasi layanan (TC-01)**
```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"client_id":"CLI-001","message":"Berapa biaya paket SEO domestik?"}'
```
```json
{
  "conversation_id": "conv-3f9a1c2b7d10",
  "client_id": "CLI-001",
  "reply": "Informasi Layanan SEO\nPaket SEO Domestik: Rp600.000 per bulan. ...",
  "detected_intent": "knowledge_query",
  "source": "llm"
}
```
`source` bernilai `llm` bila kalimat ditulis ulang LLM, dan `rules` bila jawaban deterministik.

**Aktivasi saat belum lunas (TC-03)**
```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"client_id":"CLI-001","message":"Tolong aktivasi domain resmi saya"}'
```
Balasan menolak aktivasi dan menyebut `Rp800.000` (diambil dari database). Untuk `CLI-002` (lunas) balasannya menyatakan permintaan diteruskan ke tim terkait.

**Klaim pembayaran (TC-05/06)** â†’ `detected_intent` = `payment_claim` / `status_change_request` / `prompt_injection`. Invoice tidak berubah dan balasan meminta data verifikasi.

**Riwayat sesi**
```bash
curl http://127.0.0.1:8000/conversations/conv-3f9a1c2b7d10 -H "X-Client-ID: CLI-001"
```
```json
{"conversation_id":"conv-3f9a1c2b7d10","client_id":"CLI-001","created_at":"...","updated_at":"...",
 "messages":[{"turn_index":1,"sender":"user","message_text":"...","detected_intent":"knowledge_query","created_at":"..."},
             {"turn_index":2,"sender":"assistant","message_text":"...","detected_intent":"knowledge_query","created_at":"..."}]}
```

**Konfirmasi pembayaran (validasi TC-09)**
```bash
curl -X POST http://127.0.0.1:8000/payments/confirmations -H "Content-Type: application/json" \
  -d '{"client_id":"CLI-001","invoice_no":"INV-2026-001","nominal_transfer":800000,"bank_tujuan":"BCA","nama_rekening_pengirim":"Budi Santoso"}'
# 201 {"id":1,"status":"pending","message":"Konfirmasi diterima dan menunggu verifikasi ..."}
# nominal_transfer 0 atau -1 -> 422
```

**Verifikasi oleh admin (mengubah status invoice)**
```bash
curl -X POST http://127.0.0.1:8000/admin/payment-confirmations/1/approve -H "X-Admin-Key: <ADMIN_API_KEY>"
```

## Aturan bisnis yang diterapkan

- Sisa tagihan = `total_amount - amount_paid` (min. 0). Status yang diharapkan: `paid` jika `amount_paid >= total`, `unpaid` jika 0, selain itu `half_paid`.
- Invoice dengan status yang tidak cocok dengan nominalnya **tidak dipercaya**. Chatbot tidak memproses aktivasi, tetapi menyerahkan ke tim support. `/billing` menandainya (`is_consistent: false`).
- Aktivasi hanya diteruskan bila **seluruh** invoice klien lunas. Invoice dicari dari `client_id` sesi, bukan dari klaim di teks pesan.
- Konfirmasi pembayaran: `nominal_transfer` tidak boleh melebihi sisa tagihan (pembayaran sebagian diperbolehkan). Invoice milik klien lain diperlakukan sebagai "tidak ditemukan".
- Knowledge base memengaruhi jawaban bot, jadi `POST /knowledge-bases` dibatasi untuk admin.
- Tidak ada KB yang cocok â†’ jawaban fallback persis seperti di soal, tanpa karangan LLM.

## Struktur folder

```
main.py                  entry point (uvicorn main:app)
init_db.py               buat tabel + seed (--reset untuk ulang)
db/schema.sql, seed.sql  skema dan data simulasi (idempotent)
app/
  factory.py             create_app(): wiring router, error handler, DB init
  config.py              Settings dari env/.env
  database.py            koneksi SQLite, init, transaksi
  repositories.py        semua SQL
  schemas.py             model Pydantic (termasuk PaymentConfirmationRequest)
  errors.py, deps.py     error domainâ†’HTTP, dependency (DB per-request, admin key)
  routers/               health, chat, billing(+payments/admin), conversations, knowledge
  services/
    billing.py           hitung sisa/total, konsistensi status
    payments.py          validasi berbasis DB, review admin
    intent.py            intent detection (rules)
    knowledge.py         retrieval keyword berbobot
    policy.py            policy gate + penyusunan draft dari data DB
    llm.py               GeminiClient (timeout/retry/circuit breaker), MockLLM
    chat_engine.py       orkestrasi alur + validasi tulisan ulang LLM
tests/                   pytest (TC-01..TC-10 dan lainnya)
```

## Konfigurasi (`.env`)

| Variabel | Default | Keterangan |
|---|---|---|
| `LLM_PROVIDER` | `gemini` jika key ada, selain itu `mock` | `gemini` / `mock` |
| `GEMINI_API_KEY` | â€“ | API key Google AI Studio |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Model Gemini |
| `LLM_TIMEOUT_SECONDS` / `LLM_MAX_RETRIES` | `8` / `1` | Timeout per percobaan dan jumlah retry (429/5xx/timeout) |
| `DATABASE_PATH` | `chatbot.db` | File SQLite |
| `ADMIN_API_KEY` | â€“ | Kosong â†’ endpoint admin nonaktif |

## Keterbatasan

- Intent detection berbasis aturan (regex), cukup untuk skenario soal tetapi tidak menangkap semua variasi bahasa. Pada produksi bisa dilengkapi classifier LLM yang hasilnya tetap divalidasi backend.
- Retrieval berupa keyword matching, bukan embedding.
- Otentikasi klien sebatas `client_id` (sesuai soal). Produksi memerlukan token per klien. Lihat `DEBUGGING.md` kasus 1.
