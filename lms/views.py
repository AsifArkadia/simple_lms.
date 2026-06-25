import csv
from django.contrib import messages
from django.db.models import Avg, Count, Max, Min
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from .models import Course, Member, Content, Comment, Completion


# =========================
# ROLE CHECK
# =========================
def admin_only(user):
    return user.is_superuser


# =========================
# DASHBOARD
# =========================
@login_required
def dashboard(request):
    if request.user.is_superuser:
        context = {
            'total_courses': Course.objects.count(),
            'total_users': User.objects.count(),
            'total_members': Member.objects.count(),
            'total_contents': Content.objects.count(),

            # tambahan penting
            'members_per_course': Course.objects.annotate(
                total_member=Count('member')
            ),

            'top_courses': Course.objects.annotate(
                total_member=Count('member')
            ).order_by('-total_member')[:5],
        }
        return render(request, 'dashboard_admin.html', context)

    # MAHASISWA
    else:
        total_courses = Course.objects.count()
        my_courses = Member.objects.filter(user=request.user).count()

        return render(request, 'dashboard_user.html', {
            'total_courses': total_courses,
            'my_courses': my_courses
        })


# =========================
# IMPORT CSV (ADMIN ONLY)
# =========================
@login_required
@user_passes_test(admin_only)
def import_courses(request):
    if request.method == 'POST':
        file = request.FILES.get('file')

        if not file or not file.name.endswith('.csv'):
            messages.error(request, 'File harus CSV!')
            return redirect('course_list')

        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        next(reader)  # skip header

        for row in reader:
            Course.objects.create(
                title=row[0],
                description=row[1]
            )

        messages.success(request, 'Import course berhasil!')
        return redirect('course_list')

    return render(request, 'courses/import.html')


# =========================
# KRS (MAHASISWA)
# =========================
@login_required
def krs_view(request):
    courses = Course.objects.all()
    my_courses = Member.objects.filter(user=request.user)

    return render(request, 'krs.html', {
        'courses': courses,
        'my_courses': my_courses
    })


@login_required
def ambil_course(request, id):
    course = get_object_or_404(Course, id=id)

    Member.objects.get_or_create(
        user=request.user,
        course=course
    )

    messages.success(request, "Berhasil mengambil mata kuliah!")
    return redirect('krs')


@login_required
def hapus_krs(request, id):
    member = get_object_or_404(Member, id=id, user=request.user)
    member.delete()

    messages.success(request, "Mata kuliah berhasil dihapus!")
    return redirect('krs')


# =========================
# MATERI & KOMENTAR (MAHASISWA)
# =========================
@login_required
def materi_view(request):
    members = Member.objects.filter(user=request.user).select_related('course')

    courses_data = []
    for member in members:
        contents = Content.objects.filter(course=member.course)
        content_data = []
        for content in contents:
            comments = content.comment_set.select_related('member__user').order_by('id')
            content_data.append({'content': content, 'comments': comments})

        courses_data.append({'course': member.course, 'contents': content_data})

    return render(request, 'materi.html', {'courses_data': courses_data})


@login_required
def tambah_komentar(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    member = Member.objects.filter(user=request.user, course=content.course).first()

    if not member:
        messages.error(request, "Anda belum mengikuti course materi ini.")
        return redirect('materi')

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(member=member, content=content, text=text)
            messages.success(request, "Komentar berhasil ditambahkan!")

    return redirect('materi')


# =========================
# COURSE (ADMIN ONLY)
# =========================
@login_required
@user_passes_test(admin_only)
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/list.html', {'courses': courses})


@login_required
@user_passes_test(admin_only)
def course_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')

        Course.objects.create(title=title, description=description)
        messages.success(request, "Course berhasil ditambahkan!")

        return redirect('course_list')

    return render(request, 'courses/create.html')


@login_required
@user_passes_test(admin_only)
def course_update(request, id):
    course = get_object_or_404(Course, id=id)

    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        course.save()

        messages.success(request, "Course berhasil diupdate!")
        return redirect('course_list')

    return render(request, 'courses/update.html', {'course': course})


@login_required
@user_passes_test(admin_only)
def course_delete(request, id):
    course = get_object_or_404(Course, id=id)
    course.delete()

    messages.success(request, "Course berhasil dihapus!")
    return redirect('course_list')


# =========================
# COURSES API DEMO (PERTEMUAN 10)
# =========================
def courses_api_demo(request):
    return render(request, 'courses/api_list.html')


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


# =========================
# DATA LAIN (OPTIONAL ADMIN)
# =========================
@login_required
@user_passes_test(admin_only)
def member_list(request):
    data = Member.objects.all()
    return render(request, 'list.html', {'title': 'Members', 'data': data})


@login_required
@user_passes_test(admin_only)
def content_list(request):
    data = Content.objects.all()
    return render(request, 'list.html', {'title': 'Contents', 'data': data})


@login_required
@user_passes_test(admin_only)
def comment_list(request):
    data = Comment.objects.all()
    return render(request, 'list.html', {'title': 'Comments', 'data': data})


@login_required
@user_passes_test(admin_only)
def completion_list(request):
    data = Completion.objects.all()
    return render(request, 'list.html', {'title': 'Completions', 'data': data})


@login_required
@user_passes_test(admin_only)
def user_list(request):
    data = User.objects.all()
    return render(request, 'list.html', {'title': 'Users', 'data': data})