from django.contrib import admin

from .models import FaceEmbedding, AISession


@admin.register(FaceEmbedding)
class FaceEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('student', 'source', 'model_version', 'quality', 'created_at')
    list_filter = ('source', 'model_version')
    search_fields = ('student__full_name', 'student__roll_number')


@admin.register(AISession)
class AISessionAdmin(admin.ModelAdmin):
    list_display = ('student_class', 'subject', 'date', 'teacher',
                    'recognized_count', 'unrecognized_count', 'created_at')
    list_filter = ('date',)
