from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from lms.views import *
from lms.apiv1 import apiv1

urlpatterns = [
    # =========================
    # ADMIN
    # =========================
    path('admin/', admin.site.urls),

    # =========================
    # PROFILING (django-silk)
    # =========================
    path('silk/', include('silk.urls', namespace='silk')),

    # =========================
    # REST API (Django Ninja)
    # =========================
    path('api/v1/', apiv1.urls),

    # =========================
    # AUTH
    # =========================
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='/login/'
    ), name='logout'),

    # =========================
    # DASHBOARD / LANDING PAGE
    # (publik kalau belum login, dashboard kalau sudah login)
    # =========================
    path('', dashboard, name='dashboard'),

    # =========================
    # COURSES (ADMIN)
    # =========================
    path('courses/', login_required(course_list), name='course_list'),
    path('courses/create/', login_required(course_create), name='course_create'),
    path('courses/update/<int:id>/', login_required(course_update), name='course_update'),
    path('courses/delete/<int:id>/', login_required(course_delete), name='course_delete'),
    path('courses/import/', login_required(import_courses), name='import_courses'),
    path('courses-api/', courses_api_demo, name='courses_api_demo'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

    # =========================
    # STATISTICS (ADMIN)
    # =========================
    path('stats/courses/', login_required(course_stats), name='course_stats'),
    path('stats/users/', login_required(user_stats), name='user_stats'),

    # =========================
    # DATA (ADMIN)
    # =========================
    path('members/', login_required(member_list), name='member_list'),
    path('contents/', login_required(content_list), name='content_list'),
    path('comments/', login_required(comment_list), name='comment_list'),
    path('completions/', login_required(completion_list), name='completion_list'),
    path('users/', login_required(user_list), name='user_list'),

    # =========================
    # KRS (MAHASISWA)
    # =========================
    path('krs/', login_required(krs_view), name='krs'),
    path('krs/ambil/<int:id>/', login_required(ambil_course), name='ambil_course'),
    path('krs/hapus/<int:id>/', login_required(hapus_krs), name='hapus_krs'),

    # =========================
    # MATERI & KOMENTAR (MAHASISWA)
    # =========================
    path('materi/', login_required(materi_view), name='materi'),
    path('materi/komentar/<int:content_id>/', login_required(tambah_komentar), name='tambah_komentar'),
]