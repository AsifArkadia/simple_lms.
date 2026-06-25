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
