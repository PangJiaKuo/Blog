# comments/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse


class Comment(models.Model):
    """评论"""
    article = models.ForeignKey(
        'blog.Article',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True,
        blank=True
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # 评论内容
    content = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=True)
    is_spam = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)

    # 用户信息（用于游客评论）
    guest_name = models.CharField(max_length=50, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_website = models.URLField(blank=True)

    # 统计
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 用户代理信息
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-is_pinned', 'created_at']
        indexes = [
            models.Index(fields=['article', 'created_at']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        if self.author:
            return f'Comment by {self.author} on {self.article}'
        return f'Comment by {self.guest_name} on {self.article}'

    def get_absolute_url(self):
        return f"{self.article.get_absolute_url()}#comment-{self.id}"

    def is_reply(self):
        return self.parent is not None

    def get_author_name(self):
        return self.author.username if self.author else self.guest_name

    def save(self, *args, **kwargs):
        # 如果是回复，更新父评论的回复计数
        if self.parent and self.pk is None:
            self.parent.reply_count += 1
            self.parent.save(update_fields=['reply_count'])

        super().save(*args, **kwargs)


class CommentLike(models.Model):
    """评论点赞"""
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['comment', 'user']

    def __str__(self):
        return f"{self.user} likes comment {self.comment.id}"
