from django.contrib import admin
from .models import Post, Like, Bookmark, Comment, Share, Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'posts_count', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name']
    
    def posts_count(self, obj):
        return obj.posts.count()
    posts_count.short_description = "사용된 포스트 수"

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content_preview', 'tags_preview', 'created_at']
    list_filter = ['embed_style', 'created_at', 'tags']
    search_fields = ['content', 'user__my_ID']
    filter_horizontal = ['tags']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "내용 미리보기"
    
    def tags_preview(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()[:3]])
    tags_preview.short_description = "태그"

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'journal', 'created_at']
    search_fields = ['user__my_ID']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'journal', 'created_at']
    search_fields = ['user__my_ID']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'journal', 'parent', 'content_preview', 'created_at']
    search_fields = ['content', 'user__my_ID']
    
    def content_preview(self, obj):
        return obj.content[:30] + "..." if len(obj.content) > 30 else obj.content
    content_preview.short_description = "댓글 미리보기"

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'journal', 'created_at']
    search_fields = ['user__my_ID']