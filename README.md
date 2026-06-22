# Apple Developer Academy — Simulation Test

Aplikasi latihan tes berbasis Streamlit untuk persiapan seleksi Apple Developer Academy.

## Fitur

- Registrasi akun, login, logout, dan password hash PBKDF2.
- Penyimpanan otomatis seluruh hasil tes dan jawaban pengguna.
- Dashboard grafik perkembangan nilai dari tes pertama hingga terbaru.
- Perbandingan kenaikan/penurunan, nilai rata-rata, dan personal best.
- Evaluasi section terkuat, section prioritas, serta konsep yang sering salah.
- Riwayat tes lengkap dengan nilai, jumlah jawaban benar, dan durasi.
- Alur tes lengkap: instruksi, pengerjaan, konfirmasi submit, dan hasil.
- 100 soal acak per sesi, termasuk 25 soal analisis pseudocode.
- Tujuh section: Logic, Swift, Analisis Pseudocode, Analisis Kode, Lengkapi Kode, OOP, serta Design & UX.
- Pseudocode mencakup rekursi, loop, array, sorting, searching, stack/queue, dan kompleksitas.
- Soal analisis menilai output, alur eksekusi, value/reference semantics, optional, closure, dan error handling.
- Tingkat kesulitan dan konsep ditampilkan pada soal analisis kode.
- Timer 120 menit yang memperbarui tampilan setiap detik.
- Satu soal per layar, navigasi sebelumnya/berikutnya, dan palet soal.
- Flag soal untuk ditinjau ulang dengan status navigasi kuning.
- Status navigasi berbeda untuk soal aktif, di-flag, terjawab, dan belum dijawab.
- Hasil per section dan review jawaban benar, salah, atau kosong.
- Pembahasan singkat untuk membantu memahami cara menjawab.
- Tombol **Tes Lagi** untuk membuat paket soal acak baru.

## Menjalankan aplikasi

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Kemudian buka alamat lokal yang ditampilkan Streamlit, biasanya `http://localhost:8501`.

## Struktur proyek

```text
app.py                  UI, alur tes, timer, dan penilaian
questions.py            Bank soal dan pembahasan
database.py             Akun, autentikasi, dan riwayat progres SQLite
requirements.txt        Dependensi deployment
assets/                 Logo aplikasi dalam format SVG dan PNG
scripts/                Generator aset logo PNG
.streamlit/config.toml  Tema aplikasi
```

## Penyimpanan data

Secara default data disimpan pada `data/academy_prep.db`. SQLite cocok untuk penggunaan lokal atau server dengan persistent disk. Untuk deployment publik di layanan yang filesystem-nya sementara, pindahkan database ke PostgreSQL atau Supabase agar akun dan progres tidak hilang saat aplikasi restart.
