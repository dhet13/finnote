from django.db import models
from django.contrib.auth.models import User

class JournalPost(models.Model):


    user = models.ForeignKey(User, on_delete=models.CASCADE)

    ASSET_CLASS_CHOICES = [
        ('stock', '주식'),
        ('realestate', '부동산'),
    ]
    asset_class = models.CharField(max_length=20, choices=ASSET_CLASS_CHOICES)
    
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'likes_table'

class Bookmark(models.Model):
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'bookmarks_table'

class Comment(models.Model):
    journal = models.ForeignKey(JournalPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)  # PARENT_ID
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        ordering = ['created_at']
        db_table = 'comments_table'