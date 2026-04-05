System Architecture Document (SAD) - Aegis-Motion Platform

1. Pendahuluan

Dokumen ini mendefinisikan arsitektur teknis untuk platform Aegis-Motion, sistem otomatisasi "Text-to-Animation" yang mensimulasikan kru produksi film digital menggunakan orkestrasi multi-agen (LangGraph) dan mesin render Godot 4.3.

2. Gambaran Umum Arsitektur

Sistem ini dibangun dengan model Decoupled Orchestration, di mana logika kecerdasan dipisahkan dari proses eksekusi visual.

2.1 Komponen Utama

Brain Layer (LangGraph): Mengelola state animasi dan logika keputusan kru film.

Asset Layer (AI Cloud): Integrasi API untuk generasi gambar dan pemrosesan aset (Pillow, Rembg).

Execution Layer (Godot 4.3): Engine render headless yang menerima instruksi JSON dan menghasilkan frame visual.

Bridge Layer: Mekanisme pertukaran data berbasis file (JSON Contract) antara Python dan Godot.

3. Alur Kerja Kru Film (Agentic Pipeline)

Arsitektur ini mengikuti alur Sequential-Iterative Loop:

Tahap 1: Pra-Produksi (Orchestration)

The Director: Menerima input user dan menghasilkan Shot List serta Director’s Treatment.

Lead Animator: Menyiapkan aktor dengan memicu agen pembuat aset dan konverter spritesheet.

Tahap 2: Produksi Digital (Set & Layout)

Production Designer: Membangun geometri panggung (CSG) di Godot berdasarkan koordinat meteran.

Gaffer & Cinematographer: Mengatur pencahayaan suasana dan sudut pandang kamera (FOV, Movement) dalam file konfigurasi.

Tahap 3: Eksekusi & Render

Sistem menjalankan subproses Godot dalam mode --headless.

Godot memparsing JSON, membangun scene secara dinamis, dan mengekspor screenshot preview (dailies).

Tahap 4: Pasca-Produksi & Audit

Visual Auditor: Meninjau screenshot hasil render. Jika ditemukan glitch (kaki melayang, clipping), agen ini mengirim instruksi koreksi balik ke tahap Produksi.

4. Komunikasi Data (The Bridge Protocol)

Komunikasi antar agen dan engine render dilakukan melalui JSON Data Contract.

4.1 Skema Pertukaran Data

Instruksi yang dikirim ke Godot mencakup:

set_design: Daftar node CSG, posisi, dan operasi boolean.

camera: Parameter FOV, posisi awal, target look_at, dan tipe pergerakan (Dolly/Pan).

lighting: Konfigurasi warna, energi cahaya, dan efek atmosfer (Fog).

timeline: Urutan animasi aktor dan pergerakan kamera terhadap waktu.

5. Tumpukan Teknologi (Tech Stack)

Komponen

Teknologi

Deskripsi

Orchestrator

LangGraph (Python)

State machine untuk manajemen kru film.

LLM (Logic)

Gemini 1.5 Pro

Otak utama untuk Director, Architect, dan DP.

LLM (Vision)

GPT-4 Vision / Gemini Flash

Digunakan oleh Visual Auditor untuk cek glitch.

Render Engine

Godot 4.3 (Headless)

Mesin render utama untuk simulasi 2.5D.

Image Gen

DALL-E 3 / Imagen

Penyedia aset aktor dan background.

Image Processing

Pillow & Rembg

Pembuatan spritesheet dan pembersihan latar belakang.

Final Export

FFmpeg

Penggabungan frame hasil render menjadi file .mp4.

6. Strategi Self-Healing & Penanganan Kasus Tepi (Edge Cases)

Sistem ini memiliki kemampuan pemulihan otonom melalui Audit Loop:

Z-Fighting / Clipping: Jika Auditor mendeteksi tumpang tindih mesh, Architect akan diperintahkan untuk menggeser objek sebesar 0.1 unit pada sumbu yang bermasalah.

Actor Out of Frame: Cinematographer akan menyesuaikan target kamera secara otomatis untuk mengunci posisi aktor kembali.

Low Contrast: Gaffer diperintahkan untuk meningkatkan lighting_energy jika frame terdeteksi terlalu gelap oleh Auditor.

7. Skalabilitas

Arsitektur ini mendukung skalabilitas horisontal dengan menjalankan beberapa instansi Godot Headless secara paralel untuk memproses shot-shot yang berbeda dalam satu film secara bersamaan.