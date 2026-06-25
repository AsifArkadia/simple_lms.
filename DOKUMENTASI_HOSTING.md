# Dokumentasi Hosting — Deploy ke Railway

Project: Simple LMS
Tujuan: deploy project ini ke Railway untuk keperluan demo/presentasi UAS.

> Catatan: bagian ini mendokumentasikan **persiapan kode** (sudah selesai & teruji lokal) dan **langkah deploy** (dilakukan oleh Anda sendiri, karena butuh akun GitHub/Railway pribadi).

---

# Bagian 1 — Persiapan Kode (Sudah Dikerjakan)

## 1.1 `requirements.txt` (diubah)

Menambahkan dependency yang dibutuhkan untuk produksi:
```
gunicorn
whitenoise
dj-database-url
```
- `gunicorn` — web server produksi (pengganti `manage.py runserver`)
- `whitenoise` — menyajikan static file (CSS) tanpa perlu konfigurasi server terpisah
- `dj-database-url` — supaya `DATABASES` bisa baca dari env var `DATABASE_URL` (kalau nanti mau tambah PostgreSQL)

## 1.2 `config/settings.py` (diubah)

**a) `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` dari environment variable:**
```python
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-...')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
```
Default-nya dibuat supaya **lokal tetap berjalan seperti biasa** (DEBUG=True tanpa perlu set apapun). Di Railway, env var ini diisi lewat dashboard.

**b) WhiteNoise middleware** (ditambahkan tepat setelah `SecurityMiddleware`):
```python
MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    ...
]
```

**c) Static files untuk produksi:**
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
```

**d) Database fleksibel (SQLite default, bisa diganti `DATABASE_URL`):**
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}
```

## 1.3 `Procfile` (file baru)

```
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn config.wsgi --bind 0.0.0.0:$PORT
```
- `release` dijalankan otomatis oleh Railway setiap deploy (migrasi DB + kumpulkan static file)
- `web` adalah command utama menjalankan aplikasi

## 1.4 `.gitignore` (diubah)

Ditambahkan `staticfiles/`, `.env`, dan `.claude/` (folder lokal tooling) agar tidak ikut commit.

## 1.5 Git repository

Project ini sebelumnya **belum jadi git repo**. Sudah dijalankan:
```bash
git init
git add .
git commit -m "Initial commit: Simple LMS ..."
```
Saat ini ada **1 commit awal** di branch `master`, belum terhubung ke remote/GitHub manapun.

---

# Bagian 2 — Hasil Pengujian Lokal (Sudah Diverifikasi)

| Pengujian | Hasil |
|---|---|
| `python manage.py check` | ✅ OK |
| `python manage.py collectstatic --noinput` | ✅ 228 file berhasil dikumpulkan |
| `python manage.py test lms` | ✅ 10/10 test OK |
| `runserver` dengan `DEBUG=False` + `ALLOWED_HOSTS` di-set | ✅ Login, static CSS (lewat WhiteNoise), dan API semua 200 |
| Request dengan `Host` header yang **tidak** ada di `ALLOWED_HOSTS` | ✅ Ditolak 400 (membuktikan proteksi `ALLOWED_HOSTS` berfungsi) |
| `gunicorn` di lokal (Windows) | ⚠️ Tidak bisa dites (gunicorn butuh modul `fcntl`, khusus Linux) — akan berjalan normal di Railway karena environment-nya Linux |

---

# Bagian 3 — Langkah Deploy ke Railway (Dilakukan Sendiri)

## Langkah 1 — Push ke GitHub
1. Buat repository baru di GitHub (boleh private), misal `simple-lms`.
2. Dari folder project:
   ```bash
   git remote add origin https://github.com/<username>/simple-lms.git
   git branch -M main
   git push -u origin main
   ```

## Langkah 2 — Buat Project di Railway
1. Daftar/login ke [railway.com](https://railway.com) pakai akun GitHub.
2. **New Project** → **Deploy from GitHub repo** → pilih repo `simple-lms`.
3. Railway akan otomatis mendeteksi `requirements.txt` & `Procfile` (lewat Nixpacks) dan mulai build.

## Langkah 3 — Set Environment Variables
Di tab **Variables** project Railway, tambahkan:

| Key | Value |
|---|---|
| `SECRET_KEY` | string acak panjang, contoh hasil `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | domain yang diberikan Railway, contoh `simple-lms.up.railway.app` (lihat di tab **Settings → Networking** setelah domain ter-generate) |

## Langkah 4 — Generate Domain
Di tab **Settings → Networking**, klik **Generate Domain** untuk mendapat URL publik (`https://....up.railway.app`). Masukkan domain ini ke `ALLOWED_HOSTS` (Langkah 3), lalu redeploy.

## Langkah 5 — Generate JWT Signing Key
File `jwt-signing.pem`/`.pub` sengaja tidak ikut di-commit (rahasia). Setelah deploy pertama berhasil, generate lewat shell Railway:
1. Buka tab **Deployments** → klik deployment aktif → **View Logs** / gunakan **Railway CLI**:
   ```bash
   railway run python manage.py make_jwt_key
   ```
   (jalankan dari komputer lokal yang sudah `railway login` & `railway link` ke project ini)

## Langkah 6 — Buat Superuser
```bash
railway run python manage.py createsuperuser
```

## Langkah 7 — Verifikasi
- Buka `https://<domain-railway>/login/` → halaman login harus tampil.
- Login dengan superuser yang baru dibuat → dashboard admin harus tampil dengan data kosong/awal.
- Buka `https://<domain-railway>/api/v1/docs` → Swagger harus tampil.
- **Catatan cold start**: kalau project idle beberapa saat, request pertama bisa lambat ±30 detik (wajar di tier gratis). Buka URL beberapa menit sebelum presentasi agar sudah "bangun".

---

# Ringkasan File yang Diubah/Ditambahkan

| File | Status |
|---|---|
| `requirements.txt` | Diubah — `+ gunicorn`, `+ whitenoise`, `+ dj-database-url` |
| `config/settings.py` | Diubah — env var untuk `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS`, WhiteNoise, `STORAGES`, `DATABASES` via `dj_database_url` |
| `Procfile` | **Baru** |
| `.gitignore` | Diubah — `+ staticfiles/`, `+ .env`, `+ .claude/` |
| Git repository | **Baru** — `git init` + 1 commit awal (belum push ke GitHub) |
