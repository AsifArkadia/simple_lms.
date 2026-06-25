from django.contrib import admin
from .models import Course, Member, Content, Completion, Comment

admin.site.register(Course)
admin.site.register(Member)
admin.site.register(Content)
admin.site.register(Completion)
admin.site.register(Comment)