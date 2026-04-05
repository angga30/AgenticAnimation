Functional Requirements Document (FRD) - Text-to-Animation Platform

Versi: 1.1

Status: Draft

Deskripsi: Dokumen ini merinci fungsi-fungsi teknis dari platform pembuatan animasi otomatis berbasis AI (Text-to-Animation) dengan integrasi Godot 4.3 dan LangGraph, menggunakan pendekatan kru film digital otonom.

1. Lingkup Fungsi Utama (Functional Scope)

Sistem ini harus mampu mengonversi satu prompt teks menjadi video animasi 2.5D melalui orkestrasi agen AI yang mensimulasikan peran kru produksi film (Sutradara, Penata Kamera, Penata Cahaya, dll) di dalam engine Godot.

2. Kebutuhan Fungsional (Functional Requirements)

2.1 Modul Manajemen Agen (Digital Film Crew Orchestration)

ID

Fitur

Deskripsi Fungsi

FR-1.1

Director Orchestrator

Sistem harus mampu membedah prompt menjadi "Director's Treatment", shot list, dan koordinasi antar kru (Cinematographer, Gaffer, Animator).

FR-1.2

State Management

Sistem harus menyimpan state global yang mencakup storyboard, meta-data suasana (mood), asset paths, dan camera/light settings.

FR-1.3

Agentic Feedback Loop

Sistem harus mendukung siklus "Retake" jika Visual Auditor mendeteksi kesalahan teknis atau estetika.

2.2 Modul Penata Artistik (Production Designer / Architect)

ID

Fitur

Deskripsi Fungsi

FR-2.1

Procedural Set Building

Agen harus merancang set 3D di Godot menggunakan operasi CSG (Union/Subtraction) berdasarkan mood shot (misal: "ruangan sempit" atau "lapangan luas").

FR-2.2

Spatial Logic & Scaling

Sistem harus memastikan tata letak objek memungkinkan pergerakan aktor tanpa hambatan dan mengikuti skala 1.0 = 1 meter.

2.3 Modul Penata Gerak (Lead Animator & Converter)

ID

Fitur

Deskripsi Fungsi

FR-3.1

Agnostic Asset Prep

Sistem harus mengelola pembuatan karakter unik dan background melalui provider AI (OpenAI/Google/SD).

FR-3.2

Performance Stitching

Mengubah gambar statis menjadi spritesheet animasi (Idle, Walk, Talk) menggunakan teknik pose transfer/warping.

FR-3.3

Actor Blocking

Menentukan titik spawn aktor dan jalur pergerakan di atas panggung 3D.

2.4 Modul Penata Kamera (Cinematographer - DP)

ID

Fitur

Deskripsi Fungsi

FR-4.1

Camera Node Control

Sistem harus mampu menentukan parameter Camera3D termasuk FOV (35mm untuk emosi, 75mm untuk aksi).

FR-4.2

Camera Movement Logic

Implementasi pergerakan kamera (Dolly, Pan, Orbit) menggunakan interpolasi Tween untuk transisi yang halus.

FR-4.3

Automated Framing

Kamera harus secara otomatis melakukan look_at() pada aktor utama untuk menjaga komposisi.

2.5 Modul Penata Cahaya (Gaffer & Atmosphere)

ID

Fitur

Deskripsi Fungsi

FR-5.1

Mood Lighting Engine

Mengatur DirectionalLight3D dan OmniLight3D berdasarkan tema (misal: "Cyberpunk" menggunakan warna Neon).

FR-5.2

Shadow Alignment

Memastikan karakter 2D billboard memproyeksikan bayangan yang akurat pada lingkungan 3D.

FR-5.3

Environment Tuning

Mengatur parameter WorldEnvironment termasuk Fog, Glow, dan Ambient Light.

2.6 Modul Audit & QC (Visual Auditor)

ID

Fitur

Deskripsi Fungsi

FR-6.1

Dailies Analysis

Menganalisis screenshot render mentah menggunakan Vision LLM untuk mengecek kontinuitas dan glitch.

FR-6.2

Aesthetic Scoring

Memberikan penilaian berdasarkan komposisi cahaya dan framing kamera.

3. Spesifikasi Data & Kontrak (Cinematic Data Contract)

Sistem wajib mengikuti struktur data yang menyertakan parameter filmis:

Input: User Prompt.

Intermediate (JSON): - camera: {fov, position, target, movement_type}

lighting: {energy, color, fog_density, sky_preset}

set_design: {csg_nodes, materials, props}

performance: {actor_id, animation, path_coords}

Output: .mp4 video hasil render Godot.

4. Kebutuhan Non-Fungsional (Non-Functional Requirements)

Performance: Render 1 shot (5-10 detik) harus selesai dalam < 30 detik.

Visual Consistency: Aset karakter harus tetap konsisten secara visual antar shot dalam satu sesi.

Autonomous Recovery: Sistem harus bisa memperbaiki kesalahan framing atau pencahayaan tanpa campur tangan user.

5. Matriks Penerimaan (Acceptance Criteria)

[ ] Sutradara berhasil memecah prompt menjadi minimal 2 shot berbeda.

[ ] Kamera melakukan pergerakan dinamis (tidak statis) selama durasi animasi.

[ ] Pencahayaan scene berubah sesuai dengan instruksi "Gaffer" (misal: suasana malam).

[ ] Karakter 2D terlihat menyatu dengan dunia 3D melalui bayangan dan lighting.

[ ] Auditor berhasil menangkap dan memperbaiki "Actor Out of Frame".