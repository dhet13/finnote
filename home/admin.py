from django.contrib import admin
from .models import JournalPost, Like, Bookmark, Comment

@admin.register(JournalPost)
class JournalPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'asset_class', 'content_preview', 'created_at']
    list_filter = ['asset_class', 'embed_style', 'created_at']
    search_fields = ['content', 'user__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "내용 미리보기"

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'journal', 'created_at']
    search_fields = ['user__username']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'journal', 'created_at']
    search_fields = ['user__username']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'journal', 'parent', 'content_preview', 'created_at']
    search_fields = ['content', 'user__username']
    
    def content_preview(self, obj):
        return obj.content[:30] + "..." if len(obj.content) > 30 else obj.content
    content_preview.short_description = "댓글 미리보기"