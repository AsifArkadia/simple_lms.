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


# =========================
# SCHEMA
# =========================
class Kalkulator(Schema):
    nil1: int
    nil2: int
    opr: str
    hasil: int = 0

    def calcHasil(self):
        hasil = self.nil1 + self.nil2
        if self.opr == '-':
            hasil = self.nil1 - self.nil2
        elif self.opr == 'x':
            hasil = self.nil1 * self.nil2

        return hasil


class Register(Schema):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str

    @field_validator('username')
    def validate_username(cls, value):
        if len(value) < 5:
            raise ValueError('Username harus lebih dari 5 karakter')
        return value

    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError('Password harus lebih dari 8 karakter')

        pattern = r'^(?=.*[A-Za-z])(?=.*\d).+$'
        if not re.match(pattern, value):
            raise ValueError('Password harus mengandung huruf dan angka')

        return value


class UserOut(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str


class UserUpdate(Schema):
    first_name: str
    last_name: str
    email: str


class CalcOut(Schema):
    nilai1: int
    nilai2: int
    operator: str
    hasil: int


class MessageOut(Schema):
    message: str


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


class CourseFilter(FilterSchema):
    search: Optional[str] = Field(None, q=['title__icontains', 'description__icontains'])


class CourseOut(Schema):
    id: int
    title: str
    description: str
    num_members: int
    num_contents: int


# =========================
# HELLO
# =========================
@apiv1.get('hello/', response=str)
def helloApi(request):
    return "Menyala abangkuh ..."


@apiv1.post('hello/', response=str)
def helloPost(request):
    if 'nama' in request.POST:
        return f"Selamat menikmati ya {request.POST['nama']}"
    return "Selamat tinggal dan pergi lagi"


# =========================
# CALCULATOR
# =========================
@apiv1.get('calc/{nil1}/{opr}/{nil2}', response=CalcOut)
def calculator(request, nil1: int, opr: str, nil2: int):
    hasil = nil1 + nil2
    if opr == '-':
        hasil = nil1 - nil2
    elif opr == 'x':
        hasil = nil1 * nil2

    return {'nilai1': nil1, 'nilai2': nil2, 'operator': opr, 'hasil': hasil}


@apiv1.post('calc', response=Kalkulator)
def postCalc(request, skim: Kalkulator):
    skim.hasil = skim.calcHasil()
    return skim


# =========================
# USERS
# =========================
@apiv1.get('users', response=List[UserOut])
def listUsers(request):
    return User.objects.all()


@apiv1.put('users/{id}', response=UserOut)
def userUpdate(request, id: int, data: UserUpdate):
    user = get_object_or_404(User, id=id)
    user.first_name = data.first_name
    user.last_name = data.last_name
    user.email = data.email
    user.save()
    return user


@apiv1.delete('users/{id}', response=MessageOut)
def userDelete(request, id: int):
    user = get_object_or_404(User, id=id)
    user.delete()
    return {"message": f"User dengan id {id} berhasil dihapus"}


# =========================
# REGISTER
# =========================
@apiv1.post('register/', response=UserOut)
def register(request, data: Register):
    """Endpoint untuk registrasi pengguna dengan validasi inputan:
    - username: minimal terdiri dari 5 karakter
    - password: minimal terdiri dari 8 karakter dan harus mengandung huruf dan angka
    """
    newUser = User.objects.create_user(
        username=data.username,
        password=data.password,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    return newUser


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
        num_members=Count('member', distinct=True),
        num_contents=Count('content', distinct=True),
    )

    if sort in ('id', '-id', 'title', '-title'):
        courses = courses.order_by(sort)

    return courses


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
