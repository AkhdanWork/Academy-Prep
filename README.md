# Apple Developer Academy — Simulation Test

Aplikasi latihan tes berbasis Streamlit untuk persiapan seleksi Apple Developer Academy.

## Fitur

- Alur tes lengkap: instruksi, pengerjaan, konfirmasi submit, dan hasil.
- 85 soal acak per sesi dengan 50 soal yang berfokus pada Swift.
- Enam section: Logic, Swift, Analisis Kode, Lengkapi Kode, OOP, serta Design & UX.
- Soal analisis menilai output, alur eksekusi, value/reference semantics, optional, closure, dan error handling.
- Tingkat kesulitan dan konsep ditampilkan pada soal analisis kode.
- Timer 90 menit yang memperbarui tampilan setiap detik.
- Satu soal per layar, navigasi sebelumnya/berikutnya, dan palet soal.
- Hasil per section dan review jawaban benar, salah, atau kosong.
- Pembahasan singkat untuk membantu memahami cara menjawab.
- Tombol **Tes Lagi** untuk membuat paket soal acak baru.

## Menjalankan aplikasi

```powershell
pip install streamlit
streamlit run app.py
```

Kemudian buka alamat lokal yang ditampilkan Streamlit, biasanya `http://localhost:8501`.

## Struktur proyek

```text
app.py                  UI, alur tes, timer, dan penilaian
questions.py            Bank soal dan pembahasan
.streamlit/config.toml  Tema aplikasi
```
