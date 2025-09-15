from django.db import models
from django.conf import settings

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)  
    is_default = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tags'
        ordering = ['-is_default', 'created_at']
    
    def __str__(self):
        return f"#{self.name}"

class JournalPost(models.Model):


    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    
    stock_trade_id = models.IntegerField(blank=True, null=True)
    re_deal_id = models.IntegerField(blank=True, null=True)
    
    EMBED_STYLE_CHOICES = [
        ('classic', '클래식'),
        ('compact', '컴팩트'),
    ]
    embed_style = models.CharField(max_length=20, choices=EMBED_STYLE_CHOICES, default='classic')
    embed_payload_json = models.JSONField()
    
    content = models.TextField()
    screenshot_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'journal_posts'


class Like(models.Model):
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'likes_table'

class Bookmark(models.Model):
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'bookmarks_table'

class Share(models.Model):
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'shares_table'

class Comment(models.Model):
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)  # PARENT_ID
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        ordering = ['created_at']
        db_table = 'comments_table'

class PostReport(models.Model):
    REPORT_REASONS = [
        ('spam', '스팸'),
        ('abuse', '욕설/비방'),
        ('inappropriate', '부적절한 내용'),
        ('fake', '허위 정보'),
        ('other', '기타'),
    ]
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('reporter', 'journal')
        db_table = 'post_reports_table'

class HiddenPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hidden_posts')
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='hidden_by_users')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'journal')
        db_table = 'hidden_posts_table'