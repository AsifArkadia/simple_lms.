# Dokumentasi Pertemuan 9 — Otentikasi dan Kontrol Akses REST API (JWT)

Project: Simple LMS
Materi: Authentication and Authorization dengan Django Ninja Simple JWT

Tujuan: menambahkan **login berbasis JWT** dan membuat endpoint yang hanya bisa diakses oleh user yang sudah login.

---

# Bagian 1 — Kode yang Ditambahkan / Diubah

## 1.1 `requirements.txt` (diubah)

Menambahkan library `django-ninja-simple-jwt`:

```
django
django-silk
django-ninja
django-ninja-simple-jwt
```

📸 **Screenshot A**: tampilan file `requirements.txt`.

---

## 1.2 `config/settings.py` (diubah)

Menambahkan `'ninja_simple_jwt'` ke `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lms',
    'silk',
    'ninja_simple_jwt',
]
```

📸 **Screenshot B**: tampilan `INSTALLED_APPS` di `config/settings.py`.

---

## 1.3 `lms/api.py` (file baru)

```python
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja_simple_jwt.auth.views.api import mobile_auth_router

# Auth dependency untuk endpoint yang membutuhkan JWT (Authorization: Bearer <token>)
apiAuth = HttpJwtAuth()

# Router bawaan ninja_simple_jwt: /auth/sign-in dan /auth/token-refresh
__all__ = ["apiAuth", "mobile_auth_router"]
```

📸 **Screenshot C**: tampilan file `lms/api.py`.

---

## 1.4 `lms/apiv1.py` (diubah — bagian baru)

**a) Import & registrasi router otentikasi** (ditambahkan di bagian atas file):

```python
from .api import apiAuth, mobile_auth_router
from .models import Comment, Content, Course, Member

apiv1 = NinjaAPI()

# Endpoint otentikasi JWT: /auth/sign-in dan /auth/token-refresh
apiv1.add_router("/auth/", mobile_auth_router)
```

**b) Schema baru** (ditambahkan di bagian SCHEMA):

```python
class ContentOut(Schema):
    id: int
    title: str


class MyCourseOut(Schema):
    course_id: int
    course_title: str
    course_description: str
    contents: List[ContentOut]


class EnrollOut(Schema):
    id: int
    user_id: int
    course_id: int
    course_title: str


class CommentIn(Schema):
    content_id: int
    text: str
```

**c) Endpoint terproteksi baru** (ditambahkan di bagian bawah file):

```python
# =========================
# COURSE MEMBERSHIP (PROTECTED, JWT)
# =========================
@apiv1.get('mycourses/', auth=apiAuth, response=List[MyCourseOut])
def getMyCourses(request):
    """Menampilkan semua course yang diikuti user beserta judul kontennya (butuh JWT)."""
    memberships = Member.objects.filter(user_id=request.user.id).select_related('course')

    result = []
    for member in memberships:
        result.append({
            'course_id': member.course.id,
            'course_title': member.course.title,
            'course_description': member.course.description,
            'contents': Content.objects.filter(course=member.course),
        })

    return result


@apiv1.post('course/{id}/enroll/', auth=apiAuth, response=EnrollOut)
def courseEnrollment(request, id: int):
    """Mendaftarkan user yang login ke course tertentu (butuh JWT)."""
    course = get_object_or_404(Course, pk=id)
    member, _ = Member.objects.get_or_create(user_id=request.user.id, course=course)

    return {
        'id': member.id,
        'user_id': member.user_id,
        'course_id': member.course.id,
        'course_title': member.course.title,
    }


# =========================
# COMMENTS (PROTECTED, JWT)
# =========================
@apiv1.post('comments/', auth=apiAuth, response=MessageOut)
def postComment(request, data: CommentIn):
    """Posting komentar pada content, hanya untuk user yang sudah enroll di course terkait (butuh JWT)."""
    content = get_object_or_404(Content, pk=data.content_id)
    member = Member.objects.filter(user_id=request.user.id, course=content.course).first()

    if member:
        Comment.objects.create(member=member, content=content, text=data.text)
        return {"message": "berhasil"}

    return {"message": "tidak boleh komentar di sini"}
```

📸 **Screenshot D**: tampilan file `lms/apiv1.py` bagian (a) import & registrasi router.
📸 **Screenshot E**: tampilan file `lms/apiv1.py` bagian (b) schema baru.
📸 **Screenshot F**: tampilan file `lms/apiv1.py` bagian (c) 3 endpoint terproteksi.

---

## 1.5 `.gitignore` (file baru)

```
# JWT signing keys (django-ninja-simple-jwt) - jangan commit, bersifat secret
jwt-signing.pem
jwt-signing.pub

# Python
__pycache__/
*.pyc

# Django
db.sqlite3
```

📸 **Screenshot G**: tampilan file `.gitignore`.

---

# Bagian 2 — Langkah Menjalankan & Pengujian

## Langkah 1 — Rebuild Container

```bash
docker compose down
docker compose up -d --build
```

📸 **Screenshot 1**: terminal setelah `docker compose up -d --build` selesai (container berjalan, library baru terinstall).

---

## Langkah 2 — Generate Kunci JWT

Setiap token JWT ditandatangani dengan kunci rahasia. Generate sekali saja:

```bash
docker compose exec web python manage.py make_jwt_key
```

Akan muncul 2 file baru: `jwt-signing.pem` (privat) dan `jwt-signing.pub` (publik).

📸 **Screenshot 2**: terminal menampilkan `Key pair created: jwt-signing.pem, jwt-signing.pub`.

---

## Langkah 3 — Login (Sign-in)

Buka **`http://localhost:8000/api/v1/docs`**. Akan muncul 2 endpoint baru di bagian bawah:

- `POST /api/v1/auth/sign-in` → untuk login
- `POST /api/v1/auth/token-refresh` → untuk perpanjang sesi tanpa login ulang

**Cara coba:**
1. Klik `POST /api/v1/auth/sign-in` → **Try it out**
2. Isi body dengan username & password user yang sudah terdaftar, contoh:
   ```json
   {"username": "jwtuser1", "password": "rahasia123"}
   ```
3. Klik **Execute**
4. Hasilnya berupa 2 token: `access` (untuk akses endpoint, berlaku singkat) dan `refresh` (untuk minta `access` baru)
5. **Salin nilai `access` token** — akan dipakai di langkah berikutnya.

📸 **Screenshot 3**: hasil `Try it out` pada `auth/sign-in`, terlihat `access` dan `refresh` token.

---

## Langkah 4 — Endpoint Terproteksi (Wajib Login)

Ada 3 endpoint baru yang **wajib membawa token** dari langkah 3:

| Endpoint | Fungsi |
|---|---|
| `GET /api/v1/mycourses/` | Lihat course yang saya ikuti + judul materinya |
| `POST /api/v1/course/{id}/enroll/` | Daftar (enroll) ke sebuah course |
| `POST /api/v1/comments/` | Kirim komentar pada sebuah materi |

### 4.1 Coba akses tanpa login (harus ditolak)

Klik `GET /api/v1/mycourses/` → **Try it out** → **Execute** (tanpa login dulu).
Hasil yang diharapkan: **401 Unauthorized**.

📸 **Screenshot 4**: hasil `mycourses/` tanpa login → 401 Unauthorized.

### 4.2 Aktifkan token (tombol Authorize)

1. Scroll ke atas, klik tombol **🔓 Authorize** (pojok kanan atas Swagger)
2. Masukkan **token-nya saja** (tanpa kata `Bearer`), yaitu nilai `access` dari langkah 3 — Swagger otomatis menambahkan prefix `Bearer ` saat mengirim request
3. Klik **Authorize**, lalu **Close**

Sekarang semua request dari Swagger otomatis membawa token ini.

📸 **Screenshot 5**: dialog Authorize sudah terisi token dan berstatus "Authorized" (gembok tertutup).

### 4.3 Lihat course saya (sebelum enroll)

Klik `GET /api/v1/mycourses/` → **Try it out** → **Execute**.
Hasil: list kosong `[]` (karena belum ikut course apapun).

📸 **Screenshot 6**: hasil `mycourses/` setelah login → `[]`.

### 4.4 Enroll ke sebuah course

Klik `POST /api/v1/course/{id}/enroll/` → **Try it out** → isi `id` dengan id course (contoh `2`) → **Execute**.
Hasil: data pendaftaran berhasil dibuat (muncul `id`, `user_id`, `course_id`, `course_title`).

📸 **Screenshot 7**: hasil enroll course.

### 4.5 Lihat course saya (setelah enroll)

Ulangi `GET /api/v1/mycourses/` → **Execute**.
Hasil: sekarang muncul course yang baru di-enroll, lengkap dengan daftar materinya (`contents`).

📸 **Screenshot 8**: hasil `mycourses/` setelah enroll, course + content muncul.

### 4.6 Kirim komentar

Klik `POST /api/v1/comments/` → **Try it out** → isi body:
```json
{"content_id": 1, "text": "Materi yang menarik!"}
```
→ **Execute**.

- Jika user **sudah enroll** di course tempat materi (`content_id`) berada → hasil `{"message": "berhasil"}`
- Jika **belum enroll** → hasil `{"message": "tidak boleh komentar di sini"}`

📸 **Screenshot 9**: hasil komentar berhasil (`"berhasil"`).
📸 **Screenshot 10**: (opsional) hasil komentar ditolak dari user lain yang belum enroll.

---

## Langkah 5 — Refresh Token

Klik `POST /api/v1/auth/token-refresh` → **Try it out** → isi body dengan `refresh` token dari langkah 3:
```json
{"refresh": "<refresh_token>"}
```
→ **Execute**. Hasilnya `access` token baru, tanpa perlu login ulang.

📸 **Screenshot 11**: hasil `token-refresh` menampilkan `access` token baru.

---

## Langkah 6 — Pengujian Minimal via Postman

Selain Swagger, endpoint JWT ini juga diuji menggunakan **Postman** sebagai bukti API bisa dikonsumsi klien lain (bukan hanya dari Swagger UI).

### 6.1 Login (Sign-in)
- Method: `POST`
- URL: `http://localhost:8000/api/v1/auth/sign-in`
- Body → raw → JSON:
  ```json
  {"username": "jwtuser1", "password": "rahasia123"}
  ```
- **Send** → response berisi `access` dan `refresh` token.

📸 **Screenshot 12**: hasil sign-in di Postman, response berisi `access`/`refresh`.

### 6.2 Endpoint Terproteksi

Pada tab **Authorization** request, pilih **Type: Bearer Token**, isi dengan nilai `access` (Postman otomatis menambahkan prefix `Bearer` saat mengirim).

| Endpoint | Method | Body |
|---|---|---|
| `http://localhost:8000/api/v1/mycourses/` | GET | - |
| `http://localhost:8000/api/v1/course/2/enroll/` | POST | - |
| `http://localhost:8000/api/v1/comments/` | POST | `{"content_id": 1, "text": "Materi yang menarik!"}` |
| `http://localhost:8000/api/v1/courses/?search=django` | GET | - (endpoint pagination/filtering dari Pertemuan 10) |

Tanpa token / token salah → response `401 Unauthorized`. Dengan token valid → `200 OK` dengan data sesuai endpoint.

📸 **Screenshot 13**: hasil `GET mycourses/` di Postman dengan Bearer Token terisi → 200 OK.
📸 **Screenshot 14**: hasil `GET courses/?search=django` di Postman → 200 OK, response sama seperti di Swagger.

### 6.3 Refresh Token
- Method: `POST`
- URL: `http://localhost:8000/api/v1/auth/token-refresh`
- Body: `{"refresh": "<refresh_token>"}`

📸 **Screenshot 15**: hasil `token-refresh` di Postman.

> Tips Postman: di request **Sign-in**, tab **Scripts → Post-response**, bisa ditambahkan:
> ```javascript
> const data = pm.response.json();
> pm.environment.set("access_token", data.access);
> pm.environment.set("refresh_token", data.refresh);
> ```
> sehingga token otomatis tersimpan dan tinggal dipakai sebagai `{{access_token}}` di endpoint lain, tanpa copy-paste manual.

---

# Ringkasan File yang Diubah/Ditambahkan

| File | Status |
|---|---|
| `requirements.txt` | Diubah — `+ django-ninja-simple-jwt` |
| `config/settings.py` | Diubah — `+ 'ninja_simple_jwt'` di `INSTALLED_APPS` |
| `lms/api.py` | **Baru** |
| `lms/apiv1.py` | Diubah — router login + 3 endpoint terproteksi + 4 schema baru |
| `jwt-signing.pem` / `jwt-signing.pub` | **Baru** (hasil generate, rahasia) |
| `.gitignore` | **Baru** |
