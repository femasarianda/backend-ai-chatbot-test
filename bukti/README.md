# Bukti Pengujian

Hasil lengkap: [`hasil-pytest.txt`](hasil-pytest.txt) (`pytest -v`, **33 passed**).

Semua skenario ada di [`tests/test_scenarios.py`](../tests/test_scenarios.py) dan dijalankan lewat HTTP API (FastAPI `TestClient`) dengan database SQLite sementara.

## Pemetaan skenario TC-01 s/d TC-10

| ID | Skenario | Nama tes | Yang diverifikasi |
|---|---|---|---|
| TC-01 | Informasi layanan | `test_tc01_service_info` | Jawaban memuat "Rp600.000 per bulan" dari knowledge base |
| TC-02 | Informasi pembayaran | `test_tc02_bank_account` | Jawaban memuat rekening `111-222-333` a.n. PT Contoh Digital |
| TC-03 | Tagihan belum lunas | `test_tc03_unpaid_activation_rejected_with_remaining` | CLI-001 ditolak, menyebut sisa Rp800.000 |
| TC-04 | Tagihan lunas | `test_tc04_paid_activation_forwarded` | CLI-002 diteruskan ke tim terkait |
| TC-05 | Klaim pembayaran | `test_tc05_payment_claim_does_not_change_status` | Baris invoice di DB identik sebelum dan sesudah; diminta verifikasi |
| TC-06 | Prompt injection | `test_tc06_injection_and_status_change_rejected` | Permintaan ditolak; baris invoice di DB tidak berubah |
| TC-07 | Informasi tidak tersedia | `test_tc07_unknown_topic_fallback` | Jawaban fallback persis seperti di soal |
| TC-08 | Isolasi percakapan | `test_tc08_conversation_isolation` | Jawaban dan riwayat CLI-001/CLI-002 tidak tertukar; akses silang (GET/DELETE/chat) → 403 |
| TC-09 | Validasi data | `test_tc09_invalid_payment_nominal` | Nominal 0, negatif, string, dan desimal → 422 |
| TC-10 | Pengelolaan sesi | `test_tc10_session_get_and_delete` | Riwayat sesuai sesi; hapus sesi → 204 lalu 404; baris di DB terhapus |

## Bukti data percakapan tersimpan

- `test_tc10_session_get_and_delete`: setelah `/chat`, tabel `chat_messages` berisi 2 baris (`turn_index` 1 dan 2, sender `user` dan `assistant`) dan 0 baris setelah sesi dihapus.
- `test_chat_creates_and_reuses_conversation`: sesi yang sama menghasilkan `turn_index` 1, 2, 3, 4 secara berurutan.

## Menjalankan ulang

```bash
pytest -v
```

Tes memakai MockLLM, jadi tidak membutuhkan API key. Jawaban dari Gemini yang sebenarnya didemokan di video dan dapat dicoba lewat Swagger UI (`/docs`).
