from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    max_members = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Kosongkan jika tanpa batas kuota peserta",
    )

    def __str__(self):
        return self.title

class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'course')

class Content(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    body = models.TextField()
    video_url = models.URLField(
        blank=True, null=True,
        help_text="Link video YouTube untuk materi ini (opsional)",
    )

    def __str__(self):
        return self.title

class Completion(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    text = models.TextField()