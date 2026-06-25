# Dokumentasi Pertemuan 7 — Profiling dan Optimasi ORM (Perbaikan)

Project: Simple LMS
Materi: Profiling dan Optimasi ORM dengan django-silk

Konteks: `django-silk` sebenarnya sudah terpasang di `INSTALLED_APPS`/`MIDDLEWARE` sejak awal project, tapi saat dicocokkan ulang dengan materi Pertemuan 7, ditemukan **2 gap nyata**:
1. URL `/silk/` **belum pernah didaftarkan** di `config/urls.py` — halaman profiling tidak bisa diakses sama sekali.
2. Template `lms/templates/stats/course_stats.html` sudah ada tapi **orphan** (tidak ada view/URL yang menyajikannya), dan **User Statistic** (yang juga diminta materi) belum dibuat sama sekali.

> Catatan adaptasi: materi memakai field `price`/`teacher` pada `Course` untuk statistik (total harga, min/max/avg price, course per teacher). Model `Course` di project ini tidak punya field tersebut — statistik diadaptasi memakai `num_members`, `num_contents`, `num_comments` (hasil `annotate`/`aggregate` dengan `Count`, `Avg`, `Max`, `Min`), sejalan dengan adaptasi yang sama dipakai di Pertemuan 10 & 11.

---

# Bagian 1 — Kode yang Ditambahkan / Diubah

## 1.1 `config/urls.py` (diubah) — wiring `/silk/`

```python
urlpatterns = [
    # =========================
    # ADMIN
    # =========================
    path('admin/', admin.site.urls),

    # =========================
    # PROFILING (django-silk)
    # =========================
    path('silk/', include('silk.urls', namespace='silk')),
    ...
```

Dan menambahkan route halaman statistik:
```python
    # =========================
    # STATISTICS (ADMIN)
    # =========================
    path('stats/courses/', login_required(course_stats), name='course_stats'),
    path('stats/users/', login_required(user_stats), name='user_stats'),
```

📸 **Screenshot A**: tampilan `path('silk/', include('silk.urls', namespace='silk'))` di `config/urls.py`.
📸 **Screenshot B**: tampilan route `stats/courses/` & `stats/users/` di `config/urls.py`.

---

## 1.2 `lms/views.py` (diubah) — Course Statistic & User Statistic

```python
from django.db.models import Avg, Count, Max, Min

# =========================
# STATISTICS (PERTEMUAN 7)
# =========================
@login_required
@user_passes_test(admin_only)
def course_stats(request):
    courses = Course.objects.annotate(
        num_members=Count('member', distinct=True),
        num_contents=Count('content', distinct=True),
        num_comments=Count('content__comment', distinct=True),
    ).order_by('-num_members')

    summary = courses.aggregate(
        total_courses=Count('id', distinct=True),
        avg_members=Avg('num_members'),
        max_members=Max('num_members'),
        min_members=Min('num_members'),
    )

    return render(request, 'stats/course_stats.html', {
        'summary': summary,
        'courses': courses,
        'most_popular': courses.first(),
        'least_popular': courses.last(),
    })


@login_required
@user_passes_test(admin_only)
def user_stats(request):
    users = User.objects.filter(is_superuser=False).annotate(
        num_courses=Count('member', distinct=True),
    ).order_by('-num_courses')

    summary = users.aggregate(
        total_users=Count('id', distinct=True),
        avg_courses=Avg('num_courses'),
    )

    return render(request, 'stats/user_stats.html', {
        'summary': summary,
        'users': users,
        'top_user': users.first(),
        'users_without_course': users.filter(num_courses=0),
    })
```

> Catatan teknis: `Count(..., distinct=True)` dipakai pada tiap field karena menggabungkan beberapa `Count()` relasi berbeda (`member`, `content`, `content__comment`) dalam satu `annotate()` bisa menyebabkan hasil saling melipatgandakan (cross-join) — bug yang sama yang ditemukan & diperbaiki di Pertemuan 11.

📸 **Screenshot C**: tampilan fungsi `course_stats` & `user_stats` di `lms/views.py`.

---

## 1.3 `lms/templates/stats/course_stats.html` (diperbaiki)

Sebelumnya menampilkan `stats.max_id`/`min_id`/`avg_id` (statistik `id`, tidak bermakna). Diganti menjadi statistik member/konten/komentar per course, dilengkapi kartu "Course Terpopuler" & "Course Paling Sepi", serta tabel detail semua course.

📸 **Screenshot D**: tampilan halaman `http://localhost:8000/stats/courses/` (kartu ringkasan + tabel detail).

---

## 1.4 `lms/templates/stats/user_stats.html` (file baru)

Halaman baru menampilkan total user non-admin, rata-rata course per user, user dengan course terbanyak, jumlah user tanpa course, dan tabel detail jumlah course per user.

📸 **Screenshot E**: tampilan halaman `http://localhost:8000/stats/users/`.

---

## 1.5 `lms/templates/dashboard_admin.html` (diubah)

Menambahkan 3 kartu navigasi baru di dashboard admin: **Course Statistics**, **User Statistics**, dan **Silk Profiling**.

📸 **Screenshot F**: dashboard admin menampilkan kartu-kartu baru tersebut.

---

# Bagian 2 — Langkah Pengujian

## Langkah 1 — Jalankan Server & Login sebagai Admin

```bash
python manage.py runserver 0.0.0.0:8000
```
Login di `http://localhost:8000/login/` dengan akun superuser.

📸 **Screenshot 1**: dashboard admin setelah login, terlihat kartu navigasi baru.

---

## Langkah 2 — Cek Halaman Silk Profiling

Buka **`http://localhost:8000/silk/`**.
Hasil yang diharapkan: halaman Silk berhasil terbuka (sebelumnya akan error 404 karena URL belum didaftarkan), menampilkan daftar request beserta jumlah query & waktu eksekusinya.

📸 **Screenshot 2**: halaman `/silk/` menampilkan log request.

---

## Langkah 3 — Cek Course Statistics

Buka **`http://localhost:8000/stats/courses/`**.
Hasil yang sudah diverifikasi (terhadap data aktual di database): `Total Course = 13`, beserta kartu Max/Min/Avg member per course, course terpopuler & paling sepi, dan tabel detail per course.

📸 **Screenshot 3**: halaman `/stats/courses/` menampilkan data di atas.

---

## Langkah 4 — Cek User Statistics

Buka **`http://localhost:8000/stats/users/`**.
Hasil yang sudah diverifikasi: `Total User (non-admin) = 5`, beserta rata-rata course per user, user dengan course terbanyak, dan tabel detail jumlah course per user.

📸 **Screenshot 4**: halaman `/stats/users/` menampilkan data di atas.

---

## Langkah 5 — Regression Check

Pastikan unit test (Pertemuan 11) tetap lulus setelah perubahan ini:
```bash
python manage.py test lms -v 1
```
Hasil: `Ran 10 tests ... OK` (tidak ada regresi).

📸 **Screenshot 5**: terminal menampilkan hasil test di atas.

---

# Ringkasan File yang Diubah/Ditambahkan

| File | Status |
|---|---|
| `config/urls.py` | Diubah — `+ path('silk/', ...)`, `+ path('stats/courses/', ...)`, `+ path('stats/users/', ...)` |
| `lms/views.py` | Diubah — `+ course_stats`, `+ user_stats` |
| `lms/templates/stats/course_stats.html` | Diperbaiki — statistik member/konten/komentar (bukan lagi statistik `id`) |
| `lms/templates/stats/user_stats.html` | **Baru** |
| `lms/templates/dashboard_admin.html` | Diubah — `+ 3 kartu navigasi baru` |
