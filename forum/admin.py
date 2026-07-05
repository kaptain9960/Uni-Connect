from django.contrib import admin
from .models import Department, Course, Thread, Reply, Tag, Vote, Bookmark, Notification


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'faculty', 'get_course_count']
    search_fields = ['name', 'code', 'faculty']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'department', 'level', 'semester', 'units', 'is_active']
    list_filter = ['department', 'level', 'semester', 'is_active']
    search_fields = ['code', 'title']


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'course', 'status', 'views', 'is_pinned', 'created_at']
    list_filter = ['status', 'is_pinned', 'course__department']
    search_fields = ['title', 'content', 'author__username']
    readonly_fields = ['views', 'created_at', 'updated_at']


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['author', 'thread', 'is_verified', 'created_at']
    list_filter = ['is_verified']


admin.site.register(Tag)
admin.site.register(Vote)
admin.site.register(Bookmark)
admin.site.register(Notification)
