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
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput && (test -f jwt-signing.pem || python manage.py make_jwt_key) && python manage.py ensure_superuser
web: gunicorn config.wsgi --bind 0.0.0.0:$PORT
```
- `release` dijalankan otomatis oleh Railway setiap deploy: migrasi DB, kumpulkan static file, generate JWT key kalau belum ada, dan buat superuser dari env var kalau belum ada
- `web` adalah command utama menjalankan aplikasi

## 1.4 `lms/management/commands/ensure_superuser.py` (file baru)

Command custom yang membaca env var `DJANGO_SUPERUSER_USERNAME`/`PASSWORD`/`EMAIL`, lalu membuat superuser **hanya jika belum ada** (idempotent — aman dipanggil di `release` setiap deploy tanpa duplikat/error). Tujuannya: supaya superuser bisa dibuat otomatis tanpa perlu akses shell/CLI Railway.

```python
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Membuat superuser dari environment variable DJANGO_SUPERUSER_USERNAME/"
        "PASSWORD/EMAIL jika belum ada. Aman dijalankan berulang kali (idempotent),"
        " jadi cocok dipanggil otomatis setiap deploy."
    )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD tidak di-set, dilewati.')
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Superuser "{username}" sudah ada, dilewati.')
            return

        User.objects.create_superuser(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" berhasil dibuat.'))
```

Sudah diuji lokal: tanpa env var → dilewati; dengan env var → superuser terbuat; dijalankan ulang → dilewati (tidak duplikat).

## 1.5 `.gitignore` (diubah)

Ditambahkan `staticfiles/`, `.env`, dan `.claude/` (folder lokal tooling) agar tidak ikut commit.

## 1.6 Git repository

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

## Langkah 3 — Generate Domain (lakukan dulu, sebelum isi Variables)
Di tab **Settings → Networking**, klik **Generate Domain** untuk mendapat URL publik, contoh `simple-lms.up.railway.app`. Catat domain ini untuk dipakai di Langkah 4.

## Langkah 4 — Set Environment Variables
Di tab **Variables** project Railway, tambahkan satu-satu (klik **New Variable**):

| Key | Value |
|---|---|
| `SECRET_KEY` | `VYNZUqXSf1O5GMqj-z7iCv8-hf0qJlu7u_Gh085p0QrvM-XsP1DPPCAoJ_UW-5xMtTI` (sudah digenerate, siap pakai — atau generate sendiri pakai `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | domain dari Langkah 3, contoh `simple-lms.up.railway.app` |
| `DJANGO_SUPERUSER_USERNAME` | username admin yang Anda inginkan, contoh `admin` |
| `DJANGO_SUPERUSER_PASSWORD` | password admin (buat yang kuat, ini akan jadi login produksi) |
| `DJANGO_SUPERUSER_EMAIL` | email apa saja, contoh `admin@example.com` |

Setelah semua variable disimpan, Railway otomatis **redeploy**.

> Tidak perlu install Railway CLI maupun jalankan command manual untuk JWT key & superuser — keduanya **otomatis dibuat saat deploy** lewat `Procfile` (lihat 1.3), karena:
> - `(test -f jwt-signing.pem || python manage.py make_jwt_key)` → generate JWT key kalau belum ada
> - `python manage.py ensure_superuser` → baca env var `DJANGO_SUPERUSER_*` di atas, buat superuser kalau belum ada (aman dijalankan berulang setiap deploy, tidak akan duplikat)

## Langkah 5 — Verifikasi
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
| `Procfile` | **Baru** — auto migrate, collectstatic, generate JWT key, ensure superuser |
| `lms/management/commands/ensure_superuser.py` | **Baru** |
| `.gitignore` | Diubah — `+ staticfiles/`, `+ .env`, `+ .claude/` |
| Git repository | **Baru** — `git init` + commit (belum push ke GitHub) |
