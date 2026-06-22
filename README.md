# Swift Programming — Simulation Test

Aplikasi latihan tes berbasis Streamlit untuk mengasah logika, Swift, OOP, dan kemampuan analisis kode.

## Fitur

- Registrasi akun, login, logout, dan password hash PBKDF2.
- Penyimpanan otomatis seluruh hasil tes dan jawaban pengguna.
- Dashboard grafik perkembangan nilai dari tes pertama hingga terbaru.
- Perbandingan kenaikan/penurunan, nilai rata-rata, dan personal best.
- Evaluasi section terkuat, section prioritas, serta konsep yang sering salah.
- Riwayat tes lengkap dengan nilai, jumlah jawaban benar, dan durasi.
- Detail riwayat tes dapat dibuka ulang untuk melihat soal, jawaban Anda, kunci jawaban, status benar/salah/kosong, dan pembahasan.
- Sinkronisasi opsional ke Firebase Firestore untuk user, attempt, section, dan detail jawaban.
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

Secara default data disimpan pada `data/academy_prep.db`. SQLite tetap menjadi penyimpanan lokal utama agar app bisa jalan tanpa konfigurasi cloud.

## Firebase

Project Firebase yang dipakai: `academyprep-62ae8`.

App ini berbasis Streamlit/Python, jadi integrasi Firebase memakai `firebase-admin`, bukan `npm install firebase`. Konfigurasi web API key dari Firebase Console tidak cukup untuk write server-side yang aman.

Untuk mengaktifkan sinkronisasi Firestore:

1. Buka Firebase Console, pilih project `academyprep-62ae8`.
2. Masuk ke Project settings > Service accounts.
3. Generate private key dan simpan file JSON di luar git, misalnya `firebase-service-account.json`.
4. Set environment variable:

```powershell
$env:FIREBASE_SERVICE_ACCOUNT_PATH="C:\path\to\firebase-service-account.json"
$env:FIREBASE_PROJECT_ID="academyprep-62ae8"
streamlit run app.py
```

Atau gunakan `.streamlit/secrets.toml`:

```toml
[firebase]
project_id = "academyprep-62ae8"
service_account_path = "C:\\path\\to\\firebase-service-account.json"
```

Saat kredensial belum dipasang, app tetap menyimpan data ke SQLite dan menampilkan warning bahwa sync Firebase belum aktif. Setelah kredensial aktif, login ke akun akan menyinkronkan user, riwayat tes, section, dan detail jawaban lokal ke Firestore.
