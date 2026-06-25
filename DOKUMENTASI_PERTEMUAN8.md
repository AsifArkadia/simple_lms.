# Dokumentasi Pertemuan 8 — REST API dengan Django Ninja

Project: Simple LMS
Materi: REST API dengan Django Ninja (Request/Response GET, POST, PUT, DELETE + Dokumentasi API)

---

## Langkah 1 — Menambahkan Library Django Ninja

File `requirements.txt` dibuat berisi:

```
django
django-silk
django-ninja
```

`docker-compose.yml` diubah agar instalasi dependency memakai `requirements.txt`:

```yaml
command: bash -c "pip install -r requirements.txt && python manage.py runserver 0.0.0.0:8000"
```

Jalankan dari terminal (di folder project):

```bash
docker compose down
docker compose up -d --build
```

📸 **Screenshot 1**: hasil terminal saat `docker compose up -d --build` selesai (terlihat proses `pip install` menginstall `django-ninja`, lalu container `django_lms` berjalan / `Watching for file changes with StatReloader`).

---

## Langkah 2 — Membuat File `lms/apiv1.py`

File baru [lms/apiv1.py](lms/apiv1.py) dibuat berisi:

- Instance `NinjaAPI()` bernama `apiv1`
- Schema (Pydantic):
  - `Kalkulator` — `nil1`, `nil2`, `opr`, `hasil` + method `calcHasil()`
  - `Register` — `username`, `password`, `email`, `first_name`, `last_name` dengan validasi:
    - `username` minimal 5 karakter
    - `password` minimal 8 karakter dan harus mengandung huruf **dan** angka
  - `UserOut` — representasi output data User (`id`, `username`, `first_name`, `last_name`, `email`)
  - `UserUpdate` — input untuk update user (`first_name`, `last_name`, `email`)
  - `CalcOut` — representasi output kalkulator GET (`nilai1`, `nilai2`, `operator`, `hasil`)
  - `MessageOut` — representasi output pesan sederhana (`message`), dipakai untuk response delete

Semua endpoint diberi `response=...` (termasuk `response=str` untuk `hello`) agar Swagger menampilkan tipe data response yang benar, bukan default `"string"`.
- Endpoint:
  | Method | URL | Fungsi |
  |---|---|---|
  | GET | `/api/v1/hello/` | `helloApi` — contoh response string |
  | POST | `/api/v1/hello/` | `helloPost` — menerima form data `nama` |
  | GET | `/api/v1/calc/{nil1}/{opr}/{nil2}` | `calculator` — kalkulasi via path parameter |
  | POST | `/api/v1/calc` | `postCalc` — kalkulasi via Schema `Kalkulator` |
  | GET | `/api/v1/users` | `listUsers` — list semua user (`UserOut`) |
  | PUT | `/api/v1/users/{id}` | `userUpdate` — update data user |
  | DELETE | `/api/v1/users/{id}` | `userDelete` — hapus user |
  | POST | `/api/v1/register/` | `register` — registrasi user baru dengan validasi |

📸 **Screenshot 2**: tampilan file `lms/apiv1.py` di editor (cukup bagian Schema dan beberapa endpoint).

---

## Langkah 3 — Mendaftarkan API ke URL Routing

File [config/urls.py](config/urls.py) ditambahkan:

```python
from lms.apiv1 import apiv1

urlpatterns = [
    path('admin/', admin.site.urls),

    # REST API (Django Ninja)
    path('api/v1/', apiv1.urls),
    ...
]
```

📸 **Screenshot 3**: tampilan file `config/urls.py` bagian yang diubah.

---

## Langkah 4 — Pengujian Request & Response (GET, POST, PUT, DELETE)

Pengujian dapat dilakukan via Swagger UI (`http://localhost:8000/api/v1/docs`) dengan tombol **Try it out**, atau via terminal `curl` / Postman. Berikut contoh hasil pengujian yang sudah dilakukan:

### 4.1 GET `/api/v1/hello/`
```bash
curl http://localhost:8000/api/v1/hello/
```
Response:
```json
"Menyala abangkuh ..."
```
📸 **Screenshot 4**: hasil Try it out endpoint `GET /api/v1/hello/` di Swagger.

### 4.2 GET `/api/v1/calc/{nil1}/{opr}/{nil2}`
```bash
curl "http://localhost:8000/api/v1/calc/10/+/20"
curl "http://localhost:8000/api/v1/calc/10/x/20"
```
Response:
```json
{"nilai1": 10, "nilai2": 20, "operator": "+", "hasil": 30}
{"nilai1": 10, "nilai2": 20, "operator": "x", "hasil": 200}
```
📸 **Screenshot 5**: hasil Try it out endpoint `GET /api/v1/calc/{nil1}/{opr}/{nil2}` (coba operator `+`, `-`, dan `x`).

### 4.3 POST `/api/v1/calc` (menggunakan Schema `Kalkulator`)
```bash
curl -X POST http://localhost:8000/api/v1/calc \
  -H "Content-Type: application/json" \
  -d '{"nil1":10,"nil2":5,"opr":"x"}'
```
Response:
```json
{"nil1": 10, "nil2": 5, "opr": "x", "hasil": 50}
```
📸 **Screenshot 6**: hasil Try it out endpoint `POST /api/v1/calc`.

### 4.4 GET `/api/v1/users`
```bash
curl http://localhost:8000/api/v1/users
```
Response:
```json
[
  {"id": 1, "username": "budi", "first_name": "", "last_name": "", "email": ""},
  {"id": 2, "username": "andi", "first_name": "", "last_name": "", "email": ""},
  {"id": 3, "username": "Arka", "first_name": "", "last_name": "", "email": ""}
]
```
📸 **Screenshot 7**: hasil Try it out endpoint `GET /api/v1/users`.

### 4.5 POST `/api/v1/register/` (dengan validasi)

**Input tidak valid** (username < 5 karakter, password < 8 karakter):
```bash
curl -X POST http://localhost:8000/api/v1/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"abc","password":"123","email":"abc@test.com","first_name":"A","last_name":"B"}'
```
Response (error validasi):
```json
{"detail":[
  {"type":"value_error","loc":["body","data","username"],"msg":"Value error, Username harus lebih dari 5 karakter"},
  {"type":"value_error","loc":["body","data","password"],"msg":"Value error, Password harus lebih dari 8 karakter"}
]}
```

**Input valid**:
```bash
curl -X POST http://localhost:8000/api/v1/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"dewi123","password":"rahasia123","email":"dewi@test.com","first_name":"Dewi","last_name":"Lestari"}'
```
Response:
```json
{"id": 4, "username": "dewi123", "first_name": "Dewi", "last_name": "Lestari", "email": "dewi@test.com"}
```
📸 **Screenshot 8**: hasil Try it out `POST /api/v1/register/` dengan input **tidak valid** (tampilkan error validasi).
📸 **Screenshot 9**: hasil Try it out `POST /api/v1/register/` dengan input **valid** (user baru berhasil dibuat).

### 4.6 PUT `/api/v1/users/{id}`
```bash
curl -X PUT http://localhost:8000/api/v1/users/4 \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Dewi","last_name":"Updated","email":"dewiupdated@test.com"}'
```
Response:
```json
{"id": 4, "username": "dewi123", "first_name": "Dewi", "last_name": "Updated", "email": "dewiupdated@test.com"}
```
📸 **Screenshot 10**: hasil Try it out `PUT /api/v1/users/{id}` (gunakan id user yang dibuat pada langkah 4.5).

### 4.7 DELETE `/api/v1/users/{id}`
```bash
curl -X DELETE http://localhost:8000/api/v1/users/4
```
Response:
```json
{"message": "User dengan id 4 berhasil dihapus"}
```
📸 **Screenshot 11**: hasil Try it out `DELETE /api/v1/users/{id}`, lalu panggil ulang `GET /api/v1/users` untuk membuktikan data sudah terhapus.

---

## Langkah 5 — Menjalankan Dokumentasi API (Swagger)

Buka browser ke:

```
http://localhost:8000/api/v1/docs
```

Akan tampil dokumentasi otomatis (Swagger/OpenAPI) berisi seluruh endpoint pada tabel Langkah 2, lengkap dengan skema request/response yang bisa langsung diuji dengan tombol **Try it out**.

📸 **Screenshot 12**: tampilan halaman `/api/v1/docs` menunjukkan daftar seluruh endpoint (`hello`, `calc`, `users`, `register`).

---

## Ringkasan File yang Diubah/Ditambahkan

| File | Keterangan |
|---|---|
| `requirements.txt` | **Baru** — menambahkan `django-ninja` |
| `docker-compose.yml` | Diubah — install dependency via `requirements.txt` |
| `lms/apiv1.py` | **Baru** — definisi NinjaAPI, Schema, dan seluruh endpoint |
| `config/urls.py` | Diubah — registrasi `apiv1.urls` ke `/api/v1/` |
