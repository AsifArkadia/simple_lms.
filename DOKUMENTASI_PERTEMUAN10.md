# Dokumentasi Pertemuan 10 — Throttling, Pagination, dan Filtering

Project: Simple LMS
Materi: Throttling, Pagination, dan Filtering pada Django Ninja

Tujuan:
1. Menambahkan **Throttling** (rate limiting), **Pagination**, dan **Filtering** pada endpoint `GET /api/v1/courses/`.
2. Melakukan pengujian otentikasi (JWT) pada endpoint tersebut.
3. Membuat halaman HTML untuk menampilkan daftar Courses dengan Search, Sorting, dan Pagination.

> Catatan adaptasi: model `Course` pada project ini hanya memiliki field `title` dan `description` (tidak ada `price`, `teacher`, `image` seperti pada contoh materi). Karena itu:
> - **Filtering** disesuaikan jadi `search` (cari di `title` & `description`).
> - **Sorting** memakai parameter `sort` (`id`, `-id`, `title`, `-title`).
> - Setiap course menampilkan `num_members` & `num_contents` (jumlah member dan konten yang terkait).
> - Endpoint `courses/` tetap memakai `auth=apiAuth` (JWT) sesuai contoh kode materi.

---

# Bagian 1 — Kode yang Ditambahkan / Diubah

## 1.1 `lms/apiv1.py` (diubah)

### a) Import baru & throttling global pada `apiv1`

```python
import re
from typing import List, Optional

from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404
from ninja import Field, FilterSchema, NinjaAPI, Query, Schema
from ninja.pagination import PageNumberPagination, paginate
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from pydantic import field_validator

from .api import apiAuth, mobile_auth_router
from .models import Comment, Content, Course, Member

apiv1 = NinjaAPI(
    throttle=[
        AnonRateThrottle('10/m'),
        AuthRateThrottle('100/m'),
    ],
)

# Endpoint otentikasi JWT: /auth/sign-in dan /auth/token-refresh
apiv1.add_router("/auth/", mobile_auth_router)
```

- `AnonRateThrottle('10/m')` → user anonim (belum login) maksimal **10 request/menit**.
- `AuthRateThrottle('100/m')` → user yang sudah login (membawa JWT) maksimal **100 request/menit**.
- Berlaku **global** untuk semua endpoint di `apiv1` (request ke-11 dst dalam 1 menit untuk anon akan ditolak).

📸 **Screenshot A**: tampilan bagian import & `apiv1 = NinjaAPI(throttle=[...])` di `lms/apiv1.py`.

---

### b) Schema baru: `CourseFilter` dan `CourseOut`

```python
class CourseFilter(FilterSchema):
    search: Optional[str] = Field(None, q=['title__icontains', 'description__icontains'])


class CourseOut(Schema):
    id: int
    title: str
    description: str
    num_members: int
    num_contents: int
```

📸 **Screenshot B**: tampilan schema `CourseFilter` dan `CourseOut` di `lms/apiv1.py`.

---

### c) Endpoint baru: `GET /api/v1/courses/` (pagination + filtering + sorting)

```python
# =========================
# COURSES (PROTECTED, JWT) - PAGINATION, FILTERING, SORTING
# =========================
@apiv1.get('courses/', auth=apiAuth, response=List[CourseOut])
@paginate(PageNumberPagination, page_size=5)
def listAllCourse(request, filters: CourseFilter = Query(...), sort: Optional[str] = None):
    """Menampilkan semua course dengan pagination (5/halaman), filter `search`, dan sorting `sort` (butuh JWT)."""
    courses = Course.objects.all()
    courses = filters.filter(courses)
    courses = courses.annotate(
        num_members=Count('member'),
        num_contents=Count('content'),
    )

    if sort in ('id', '-id', 'title', '-title'):
        courses = courses.order_by(sort)

    return courses
```

- `@paginate(PageNumberPagination, page_size=5)` → menampilkan **5 data per halaman**, diakses dengan `?page=1`, `?page=2`, dst.
- `?search=<kata kunci>` → filter berdasarkan `title` atau `description` (icontains).
- `?sort=id|-id|title|-title` → sorting naik/turun berdasarkan `id` atau `title`.
- `auth=apiAuth` → endpoint **wajib JWT**, tanpa token akan mengembalikan `401 Unauthorized`.

📸 **Screenshot C**: tampilan endpoint `listAllCourse` di `lms/apiv1.py`.

---

## 1.2 `lms/views.py` (diubah)

Menambahkan view untuk halaman HTML demo Courses (poin 3):

```python
# =========================
# COURSES API DEMO (PERTEMUAN 10)
# =========================
def courses_api_demo(request):
    return render(request, 'courses/api_list.html')
```

📸 **Screenshot D**: tampilan fungsi `courses_api_demo` di `lms/views.py`.

---

## 1.3 `config/urls.py` (diubah)

Menambahkan route untuk halaman demo:

```python
path('courses/import/', login_required(import_courses), name='import_courses'),
path('courses-api/', courses_api_demo, name='courses_api_demo'),
```

📸 **Screenshot E**: tampilan tambahan `path('courses-api/', ...)` di `config/urls.py`.

---

## 1.4 `lms/templates/courses/api_list.html` (file baru)

Halaman HTML yang memanggil `GET /api/v1/courses/` menggunakan `fetch()`, dibuat dengan **Bootstrap 5** dan gaya navbar/card yang sama seperti `dashboard_admin.html` & `courses/list.html` agar konsisten dengan dashboard lain. Fitur:
- Input **Access Token (JWT)** (disimpan di `localStorage`, dikirim sebagai header `Authorization: Bearer <token>`)
- Input **Cari Course** (kirim parameter `?search=`)
- Dropdown **Urutkan** (kirim parameter `?sort=`)
- **Pagination** Bootstrap (tombol nomor halaman, kirim parameter `?page=`)
- Tabel: ID, Nama Course, Deskripsi, Jumlah Member, Jumlah Konten

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Courses API (v1)</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        body {
            background-color: #f4f6f9;
        }

        .navbar-brand {
            font-weight: bold;
        }
    </style>
</head>
<body>

<!-- NAVBAR -->
<nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow">
    <div class="container-fluid">
        <span class="navbar-brand">📚 Courses API (v1)</span>
        <a href="/" class="btn btn-secondary btn-sm">Dashboard</a>
    </div>
</nav>

<div class="container mt-4">

    <!-- TITLE -->
    <div class="mb-4">
        <h3 class="fw-bold">Daftar Courses (API v1)</h3>
        <p class="text-muted">
            Endpoint <code>/api/v1/courses/</code> butuh JWT. Login dulu lewat
            <a href="/api/v1/docs" target="_blank">/api/v1/docs</a> (auth/sign-in),
            lalu tempel nilai <code>access</code> ke kolom Access Token di bawah.
        </p>
    </div>

    <!-- TOOLBAR -->
    <div class="card shadow mb-4">
        <div class="card-body">
            <div class="row g-3 align-items-end">
                <div class="col-md-5">
                    <label for="token" class="form-label">Access Token (JWT)</label>
                    <input type="text" id="token" class="form-control" placeholder="Tempel access token di sini">
                </div>
                <div class="col-md-3">
                    <label for="search" class="form-label">Cari Course</label>
                    <input type="text" id="search" class="form-control" placeholder="Nama / deskripsi...">
                </div>
                <div class="col-md-3">
                    <label for="sort" class="form-label">Urutkan</label>
                    <select id="sort" class="form-select">
                        <option value="">Default</option>
                        <option value="id">ID (naik)</option>
                        <option value="-id">ID (turun)</option>
                        <option value="title">Judul (A-Z)</option>
                        <option value="-title">Judul (Z-A)</option>
                    </select>
                </div>
                <div class="col-md-1">
                    <button id="btnSearch" class="btn btn-primary w-100">Cari</button>
                </div>
            </div>
        </div>
    </div>

    <!-- INFO / ERROR -->
    <div id="info" class="alert d-none"></div>

    <!-- TABLE -->
    <div class="card shadow">
        <div class="card-header bg-dark text-white">
            📊 Data Courses
        </div>
        <div class="card-body">
            <table class="table table-bordered table-striped align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Nama Course</th>
                        <th>Deskripsi</th>
                        <th class="text-center">Jumlah Member</th>
                        <th class="text-center">Jumlah Konten</th>
                    </tr>
                </thead>
                <tbody id="tbody"></tbody>
            </table>

            <ul class="pagination justify-content-center mb-0" id="pagination"></ul>
        </div>
    </div>

</div>

<script>
    const PAGE_SIZE = 5;
    let currentPage = 1;

    const tokenInput = document.getElementById('token');
    const searchInput = document.getElementById('search');
    const sortSelect = document.getElementById('sort');
    const tbody = document.getElementById('tbody');
    const pagination = document.getElementById('pagination');
    const info = document.getElementById('info');

    // simpan token di localStorage agar tidak perlu paste ulang setiap reload
    tokenInput.value = localStorage.getItem('jwt_access') || '';
    tokenInput.addEventListener('change', () => {
        localStorage.setItem('jwt_access', tokenInput.value.trim());
    });

    function showInfo(message, type) {
        if (!message) {
            info.className = 'alert d-none';
            info.textContent = '';
            return;
        }
        info.className = `alert alert-${type}`;
        info.textContent = message;
    }

    async function loadCourses(page = 1) {
        currentPage = page;
        showInfo('', null);

        const params = new URLSearchParams();
        params.set('page', page);
        if (searchInput.value.trim()) {
            params.set('search', searchInput.value.trim());
        }
        if (sortSelect.value) {
            params.set('sort', sortSelect.value);
        }

        const res = await fetch(`/api/v1/courses/?${params.toString()}`, {
            headers: {
                'Authorization': `Bearer ${tokenInput.value.trim()}`,
            },
        });

        if (res.status === 401) {
            tbody.innerHTML = '';
            pagination.innerHTML = '';
            showInfo('Token tidak valid / kosong. Login dulu lewat /api/v1/docs.', 'danger');
            return;
        }

        if (res.status === 429) {
            showInfo('Too many requests. Coba lagi sebentar.', 'warning');
            return;
        }

        const data = await res.json();
        renderTable(data.items);
        renderPagination(data.count);
    }

    function renderTable(items) {
        tbody.innerHTML = '';
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Tidak ada data.</td></tr>';
            return;
        }
        for (const c of items) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.id}</td>
                <td>${c.title}</td>
                <td>${c.description}</td>
                <td class="text-center">${c.num_members}</td>
                <td class="text-center">${c.num_contents}</td>
            `;
            tbody.appendChild(tr);
        }
    }

    function renderPagination(total) {
        pagination.innerHTML = '';
        const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
        for (let p = 1; p <= totalPages; p++) {
            const li = document.createElement('li');
            li.className = 'page-item' + (p === currentPage ? ' active' : '');

            const btn = document.createElement('button');
            btn.className = 'page-link';
            btn.textContent = p;
            btn.addEventListener('click', () => loadCourses(p));

            li.appendChild(btn);
            pagination.appendChild(li);
        }
    }

    document.getElementById('btnSearch').addEventListener('click', () => loadCourses(1));
    sortSelect.addEventListener('change', () => loadCourses(1));

    loadCourses(1);
</script>

</body>
</html>
```

📸 **Screenshot F**: tampilan file `lms/templates/courses/api_list.html` (kode).

---

# Bagian 2 — Langkah Pengujian

> **Catatan penting untuk screenshot**: karena `GET /api/v1/courses/` wajib JWT (`auth=apiAuth`), URL endpoint ini **tidak bisa dibuka langsung di tab browser baru** (browser tidak mengirim header `Authorization`, sehingga selalu muncul `{"detail": "Unauthorized"}`). Response body yang berisi data course **hanya muncul di hasil "Try it out" / Execute pada Swagger** (setelah Authorize dengan token) — gunakan tampilan tersebut untuk semua screenshot Langkah 3-7 di bawah.

## Langkah 1 — Jalankan Server

```bash
docker compose up -d --build
```

📸 **Screenshot 1**: terminal setelah server berhasil berjalan.

---

## Langkah 2 — Login untuk Mendapatkan Token

Buka **`http://localhost:8000/api/v1/docs`**, gunakan `POST /api/v1/auth/sign-in` (Try it out) seperti pada Pertemuan 9, lalu salin nilai `access` token.

📸 **Screenshot 2**: hasil sign-in menampilkan `access` & `refresh` token.

---

## Langkah 3 — Uji Otentikasi pada `GET /api/v1/courses/`

### 3.1 Tanpa token (harus ditolak)

Klik `GET /api/v1/courses/` → **Try it out** → **Execute** (tanpa Authorize).
Hasil yang diharapkan: **401 Unauthorized**.

📸 **Screenshot 3**: hasil `courses/` tanpa token → 401.

### 3.2 Dengan token (Authorize)

1. Klik tombol **🔓 Authorize**, isi **token-nya saja** (tanpa kata `Bearer` — Swagger otomatis menambahkan prefix `Bearer `), klik **Authorize** → **Close**.
2. Klik `GET /api/v1/courses/` → **Try it out** → **Execute**.

Hasil: status `200`, response berbentuk:
```json
{
  "items": [ ... 5 data course ... ],
  "count": 13
}
```

📸 **Screenshot 4**: hasil `courses/` dengan token → 200, menampilkan 5 item halaman pertama + `count`.

---

## Langkah 4 — Uji Pagination

- `GET /api/v1/courses/?page=1` → 5 data pertama.
- `GET /api/v1/courses/?page=2` → 5 data berikutnya.

📸 **Screenshot 5**: hasil `?page=1` (5 data pertama).
📸 **Screenshot 6**: hasil `?page=2` (5 data berikutnya, berbeda dari halaman 1).

---

## Langkah 5 — Uji Filtering (Search)

`GET /api/v1/courses/?search=django` → hanya menampilkan course yang judul/deskripsinya memuat kata "django".

📸 **Screenshot 7**: hasil `?search=django` → hanya course terkait Django yang muncul.

---

## Langkah 6 — Uji Sorting

`GET /api/v1/courses/?sort=-title` → data diurutkan berdasarkan judul secara menurun (Z-A).

📸 **Screenshot 8**: hasil `?sort=-title` → urutan judul terbalik dibanding default.

---

## Langkah 7 — Uji Throttling

Kirim request **berturut-turut (lebih dari 10x dalam 1 menit)** ke endpoint apapun di `/api/v1/...` sebagai anonim (tanpa token), misalnya `GET /api/v1/hello/`, dengan cara klik **Execute** berulang kali secara cepat.

Hasil yang diharapkan: setelah melewati batas 10 request/menit, response berubah menjadi:
```json
{"detail": "Too many requests."}
```
dengan status `429`.

📸 **Screenshot 9**: salah satu response awal → `200 OK`.
📸 **Screenshot 10**: response setelah melewati limit → `429` dengan pesan `"Too many requests."`.

---

## Langkah 8 — Halaman HTML Courses (Search, Sort, Pagination)

1. Buka **`http://localhost:8000/courses-api/`**.
2. Tempel `access` token (dari Langkah 2) ke kolom **Access token (JWT)**.
3. Tabel courses otomatis termuat (halaman 1, 5 data).
4. Coba ketik kata kunci di kolom **Cari**, lalu klik **Cari** → tabel terfilter.
5. Coba ubah dropdown **Urutkan** → tabel ter-sorting ulang.
6. Klik nomor halaman di bagian bawah tabel → data berganti sesuai halaman.

📸 **Screenshot 11**: halaman `courses-api/` menampilkan tabel courses halaman 1.
📸 **Screenshot 12**: hasil pencarian (search) pada halaman tersebut.
📸 **Screenshot 13**: hasil sorting pada halaman tersebut.
📸 **Screenshot 14**: tampilan setelah pindah ke halaman 2 (pagination).

---

# Ringkasan File yang Diubah/Ditambahkan

| File | Status |
|---|---|
| `lms/apiv1.py` | Diubah — throttling global, schema `CourseFilter`/`CourseOut`, endpoint `GET /api/v1/courses/` (pagination+filter+sort, JWT) |
| `lms/views.py` | Diubah — `+ courses_api_demo` |
| `config/urls.py` | Diubah — `+ path('courses-api/', ...)` |
| `lms/templates/courses/api_list.html` | **Baru** — halaman demo Search, Sort, Pagination |
