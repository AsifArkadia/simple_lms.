# Dokumentasi Pertemuan 11 — Implementasi Automated Testing

Project: Simple LMS
Materi: Automated Testing dengan Django `TestCase`

Tujuan: menulis unit test otomatis untuk model-model LMS (`Course`, `Member`, `Content`, `Comment`) menggunakan `python manage.py test`.

> Catatan adaptasi: materi memakai model `Course` (dengan `price`, `teacher`), `CourseMember` (`roles`), `CourseContent`, dan `Enrollment` (dengan `max_students`). Project ini tidak punya field/model tersebut — model aslinya adalah `Course` (`title`, `description`), `Member` (`user`, `course`), `Content` (`course`, `title`, `body`), `Comment` (`member`, `content`, `text`). Test diadaptasi ke model asli:
> - Test "harga negatif" & "course penuh (`max_students`)" **tidak dibuat** karena field tersebut tidak ada di model ini.
> - Test "duplicate enrollment" tetap dibuat, tapi membutuhkan tambahan **constraint unik** pada `Member` (lihat 1.1 di bawah).
> - Ditambahkan `CourseAnnotationTest` untuk menguji `Count()` annotation (`num_members`, `num_contents`) yang dipakai endpoint `GET /api/v1/courses/` dari Pertemuan 10 — dan dari test ini ditemukan **bug nyata** yang langsung diperbaiki (lihat 1.3).

---

# Bagian 1 — Kode yang Ditambahkan / Diubah

## 1.1 `lms/models.py` (diubah)

Menambahkan constraint **unique_together** pada `Member` supaya satu user tidak bisa terdaftar dua kali di course yang sama (constraint ini sekaligus dipakai untuk test "duplicate enrollment"):

```python
class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'course')
```

Migration dibuat dengan:
```bash
python manage.py makemigrations lms
python manage.py migrate lms
```
Menghasilkan file baru `lms/migrations/0002_alter_member_unique_together.py`.

📸 **Screenshot A**: tampilan `class Meta: unique_together = ('user', 'course')` pada `lms/models.py`.
📸 **Screenshot B**: terminal hasil `makemigrations` & `migrate`.

---

## 1.2 `lms/tests.py` (file baru — isi lengkap)

```python
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Count
from django.test import TestCase

from .models import Comment, Content, Course, Member


class CourseModelTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            title="Pemrograman Django",
            description="Belajar Django",
        )

    def test_course_creation(self):
        course = Course.objects.get(title="Pemrograman Django")

        self.assertEqual(course.description, "Belajar Django")
        self.assertEqual(str(course), course.title)


class MemberModelTest(TestCase):
    def setUp(self):
        self.student = User.objects.create(username='student1')
        self.course = Course.objects.create(title="Pemrograman Django", description="Belajar Django")

    def test_member_creation(self):
        member = Member.objects.create(user=self.student, course=self.course)

        self.assertEqual(member.user.username, 'student1')
        self.assertEqual(member.course.title, "Pemrograman Django")


class ContentModelTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(title="Pemrograman Django", description="Belajar Django")

    def test_content_creation(self):
        content = Content.objects.create(
            course=self.course,
            title="Pengenalan Django",
            body="Materi dasar tentang Django",
        )

        self.assertEqual(content.course.title, "Pemrograman Django")
        self.assertEqual(content.title, "Pengenalan Django")


class CourseQueryTest(TestCase):
    def setUp(self):
        Course.objects.create(title="Django", description="Belajar Django")
        Course.objects.create(title="Flask", description="Belajar Flask")

    def test_course_retrieval_by_title(self):
        # Query course yang judulnya memuat kata "django"
        courses = Course.objects.filter(title__icontains="django")

        self.assertEqual(courses.count(), 1)
        self.assertEqual(courses.first().title, "Django")


class CourseValidationTest(TestCase):
    def test_empty_title(self):
        # Coba membuat course tanpa judul
        course = Course(title="", description="Belajar Django")

        # Pastikan ValidationError muncul
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_title_too_long(self):
        # title max_length=100, coba isi 101 karakter
        course = Course(title="x" * 101, description="Belajar Django")

        with self.assertRaises(ValidationError):
            course.full_clean()


class CourseAnnotationTest(TestCase):
    """Menguji annotate num_members & num_contents yang dipakai endpoint GET /api/v1/courses/ (Pertemuan 10)."""

    def setUp(self):
        self.course = Course.objects.create(title="Django", description="Belajar Django")
        self.student1 = User.objects.create(username='student1')
        self.student2 = User.objects.create(username='student2')

        Member.objects.create(user=self.student1, course=self.course)
        Member.objects.create(user=self.student2, course=self.course)
        Content.objects.create(course=self.course, title="Intro", body="Materi pembuka")

    def test_member_and_content_count(self):
        course = Course.objects.annotate(
            num_members=Count('member', distinct=True),
            num_contents=Count('content', distinct=True),
        ).get(pk=self.course.pk)

        self.assertEqual(course.num_members, 2)
        self.assertEqual(course.num_contents, 1)


class MemberEnrollmentTest(TestCase):
    def setUp(self):
        self.student = User.objects.create(username='student1')
        self.course = Course.objects.create(
            title="Pemrograman Python",
            description="Kursus Python tingkat dasar",
        )

    def test_enrollment_success(self):
        # Simulasi siswa mendaftar course
        member = Member.objects.create(user=self.student, course=self.course)

        self.assertEqual(member.course.title, "Pemrograman Python")
        self.assertEqual(member.user.username, "student1")

    def test_duplicate_enrollment(self):
        # Buat enrollment pertama
        Member.objects.create(user=self.student, course=self.course)

        # Coba buat enrollment kedua dengan user dan course yang sama
        # Harus gagal karena unique_together constraint pada Member
        with self.assertRaises(IntegrityError):
            Member.objects.create(user=self.student, course=self.course)


class CommentModelTest(TestCase):
    def setUp(self):
        self.student = User.objects.create(username='student1')
        self.course = Course.objects.create(title="Django", description="Belajar Django")
        self.member = Member.objects.create(user=self.student, course=self.course)
        self.content = Content.objects.create(course=self.course, title="Intro", body="Materi pembuka")

    def test_comment_creation(self):
        comment = Comment.objects.create(
            member=self.member,
            content=self.content,
            text="Materi yang menarik!",
        )

        self.assertEqual(comment.member.user.username, "student1")
        self.assertEqual(comment.text, "Materi yang menarik!")
```

📸 **Screenshot C**: tampilan file `lms/tests.py` (kode lengkap).

---

## 1.3 `lms/apiv1.py` (diubah — bug fix dari hasil testing)

Saat menulis `CourseAnnotationTest`, ditemukan **bug nyata**: jika satu course punya lebih dari 1 member **dan** lebih dari 1 content sekaligus, `Count('member')` dan `Count('content')` dalam satu `annotate()` saling melipatgandakan hasil satu sama lain (akibat *cross join* SQL). Diperbaiki dengan menambahkan `distinct=True` pada endpoint `GET /api/v1/courses/`:

```python
courses = courses.annotate(
    num_members=Count('member', distinct=True),
    num_contents=Count('content', distinct=True),
)
```

📸 **Screenshot D**: tampilan baris `Count(..., distinct=True)` yang diperbaiki di `lms/apiv1.py`.

---

# Bagian 2 — Langkah Pengujian

## Langkah 1 — Jalankan Automated Testing

```bash
python manage.py test lms -v 2
```

(atau via Docker: `docker compose exec web python manage.py test lms -v 2`)

Hasil yang diharapkan — seluruh 10 test **OK**:

```
test_comment_creation (lms.tests.CommentModelTest.test_comment_creation) ... ok
test_content_creation (lms.tests.ContentModelTest.test_content_creation) ... ok
test_member_and_content_count (lms.tests.CourseAnnotationTest.test_member_and_content_count) ... ok
test_course_creation (lms.tests.CourseModelTest.test_course_creation) ... ok
test_course_retrieval_by_title (lms.tests.CourseQueryTest.test_course_retrieval_by_title) ... ok
test_empty_title (lms.tests.CourseValidationTest.test_empty_title) ... ok
test_title_too_long (lms.tests.CourseValidationTest.test_title_too_long) ... ok
test_duplicate_enrollment (lms.tests.MemberEnrollmentTest.test_duplicate_enrollment) ... ok
test_enrollment_success (lms.tests.MemberEnrollmentTest.test_enrollment_success) ... ok
test_member_creation (lms.tests.MemberModelTest.test_member_creation) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.023s

OK
```

📸 **Screenshot 1**: terminal menampilkan hasil `python manage.py test lms -v 2` → 10 test, semua `ok`, akhir `OK`.

---

## Langkah 2 — (Opsional) Tunjukkan Bug Sebelum Diperbaiki

Untuk dokumentasi proses, bisa ditunjukkan bahwa sebelum `distinct=True` ditambahkan, test `test_member_and_content_count` **gagal**:

```
FAIL: test_member_and_content_count (lms.tests.CourseAnnotationTest.test_member_and_content_count)
AssertionError: 2 != 1
```

Ini terjadi karena 2 member × 1 content menghasilkan 2 baris hasil JOIN sebelum di-`Count`, sehingga `num_contents` ikut terhitung 2 padahal seharusnya 1.

📸 **Screenshot 2**: (opsional) terminal menampilkan `FAIL` sebelum perbaikan `distinct=True`.

---

## Langkah 3 — Verifikasi Endpoint `GET /api/v1/courses/` Tetap Benar

Setelah fix, test ulang endpoint Pertemuan 10 secara manual (Swagger atau curl dengan token JWT) untuk course yang punya >1 member dan >1 content, pastikan `num_members` & `num_contents` sudah akurat (tidak saling kali).

📸 **Screenshot 3**: hasil `GET /api/v1/courses/` di Swagger menampilkan `num_members`/`num_contents` yang benar untuk course dengan banyak member & content.

---

# Ringkasan File yang Diubah/Ditambahkan

| File | Status |
|---|---|
| `lms/models.py` | Diubah — `+ class Meta: unique_together = ('user', 'course')` pada `Member` |
| `lms/migrations/0002_alter_member_unique_together.py` | **Baru** (hasil `makemigrations`) |
| `lms/tests.py` | Diubah — 10 unit test untuk `Course`, `Member`, `Content`, `Comment` |
| `lms/apiv1.py` | Diubah — bug fix `Count(..., distinct=True)` pada `listAllCourse` |
