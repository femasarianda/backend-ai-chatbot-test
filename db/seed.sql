-- Data simulasi (fiktif). Idempotent: INSERT OR IGNORE + UNIQUE key.
-- due_date ditambahkan (tidak ada di seeder soal) agar kolom terisi.

INSERT OR IGNORE INTO clients
(client_id, client_name, company_name, phone_number, official_domain)
VALUES
('CLI-001', 'Budi Santoso', 'PT Makmur Sentosa',
 '6281234567801', 'makmursentosa.com'),
('CLI-002', 'Rani Wijaya', 'Toko Berkah Rani',
 '6281234567802', 'tokorani.id'),
('CLI-003', 'Hendra Tan', 'CV Solusi Digital',
 '6281234567803', 'solusidigital.co.id');

INSERT OR IGNORE INTO invoices
(invoice_no, client_id, service_type, package_name,
 total_amount, amount_paid, payment_status, due_date)
VALUES
('INV-2026-001', 'CLI-001', 'website',
 'Gold Website', 1600000, 800000, 'half_paid', '2026-12-15'),
('INV-2026-002', 'CLI-002', 'seo',
 'SEO Domestik', 600000, 600000, 'paid', '2026-12-01'),
('INV-2026-003', 'CLI-003', 'website',
 'Platinum Website', 3000000, 0, 'unpaid', '2026-12-20');

INSERT OR IGNORE INTO knowledge_bases
(category, keyword_triggers, title, content)
VALUES
(
'rekening',
'rekening, transfer, bayar, bca, mandiri, bri',
'Rekening Pembayaran',
'Data rekening pembayaran resmi untuk keperluan simulasi:
BCA: 111-222-333 a.n. PT Contoh Digital.
Gunakan hanya data simulasi ini.'
),
(
'layanan',
'seo, paket seo, ranking google, search engine',
'Informasi Layanan SEO',
'Paket SEO Domestik: Rp600.000 per bulan.
Paket SEO Internasional: Rp2.200.000 per bulan.
Laporan posisi kata kunci diberikan setiap akhir bulan.'
),
(
'kebijakan',
'revisi, edit web, perbaikan, ganti foto',
'Kebijakan Revisi',
'Setiap pembuatan website mendapatkan maksimal
3 kali revisi gratis dalam waktu 1 bulan setelah pelunasan.
Revisi berikutnya dapat dikenakan biaya tambahan.'
),
(
'operasional',
'sambung domain, online, go live, domain resmi',
'Kebijakan Aktivasi Layanan',
'Aktivasi domain utama hanya dapat diproses
jika tagihan terkait telah berstatus lunas.
Estimasi proses aktivasi adalah 1x24 jam.'
);
