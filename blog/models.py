# blog/models.py
import random
import string

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager
from taggit.models import TagBase, GenericTaggedItemBase


class Category(models.Model):
    """文章分类"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CustomTag(TagBase):
    """自定义标签"""
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class TaggedArticle(GenericTaggedItemBase):
    """文章标签关联"""
    tag = models.ForeignKey(
        CustomTag,
        on_delete=models.CASCADE,
        related_name="tagged_articles"
    )


class Article(models.Model):
    """博客文章"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    title = models.CharField(max_length=200, verbose_name='标题')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL标识')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='作者'
    )
    content = RichTextField(verbose_name='内容')
    excerpt = models.TextField(max_length=500, blank=True, verbose_name='摘要')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        verbose_name='分类'
    )
    tags = TaggableManager(through=TaggedArticle, blank=True, verbose_name='标签')
    featured_image = models.ImageField(
        upload_to='article_images/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='特色图片'
    )
    is_featured = models.BooleanField(default=False, verbose_name='是否推荐')
    view_count = models.PositiveIntegerField(default=0, verbose_name='浏览量')
    like_count = models.PositiveIntegerField(default=0, verbose_name='点赞数')
    comment_count = models.PositiveIntegerField(default=0, verbose_name='评论数')
    reading_time = models.PositiveIntegerField(default=0, verbose_name='阅读时长(分钟)')

    # 文章状态
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')

    # 元信息
    meta_title = models.CharField(max_length=200, blank=True, verbose_name='SEO标题')
    meta_description = models.TextField(blank=True, verbose_name='SEO描述')
    meta_keywords = models.CharField(max_length=200, blank=True, verbose_name='SEO关键词')

    # 社交分享
    allow_comments = models.BooleanField(default=True, verbose_name='允许评论')
    allow_sharing = models.BooleanField(default=True, verbose_name='允许分享')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '文章'
        verbose_name_plural = '文章'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:article_detail', kwargs={'slug': self.slug})

    # def save(self, *args, **kwargs):
    #     # 自动生成 slug
    #     if not self.slug:
    #         self.slug = slugify(self.title)
    #
    #     # 如果状态变为已发布且没有发布时间，则设置发布时间
    #     if self.status == 'published' and not self.published_at:
    #         self.published_at = timezone.now()
    #
    #     # 计算阅读时长（假设每分钟阅读200字）
    #     word_count = len(self.content)
    #     self.reading_time = max(1, word_count // 200)
    #
    #     super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        # 1. 确保有有效的slug
        if not self.slug or not self.slug.strip() or self.slug.startswith('-'):
            base_slug = slugify(self.title) if self.title else 'untitled-article'

            # 确保base_slug有效
            if not base_slug or base_slug.startswith('-'):
                base_slug = 'article'

            # 生成唯一slug
            counter = 1
            original_slug = base_slug

            while Article.objects.filter(slug=self.slug).exclude(id=self.id).exists() or not self.slug:
                if counter == 1:
                    self.slug = original_slug
                else:
                    self.slug = f"{original_slug}-{counter - 1}"

                # 检查唯一性
                if Article.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                    counter += 1
                else:
                    break

        # 2. 设置发布时间（如果发布）
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # 3. 计算阅读时长
        if self.content:
            # 简单字数统计
            word_count = len(self.content)
            self.reading_time = max(1, word_count // 200)
            self.word_count = word_count
        else:
            self.reading_time = 1
            self.word_count = 0

        # 4. 更新时间戳
        if not self.pk:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()

        super().save(*args, **kwargs)


class ArticleLike(models.Model):
    """文章点赞"""
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['article', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} likes {self.article}"


class ArticleBookmark(models.Model):
    """文章收藏"""
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['article', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} bookmarked {self.article}"


# 在 models.py 末尾添加
class SiteSettings(models.Model):
    """站点设置模型"""
    site_name = models.CharField(max_length=100, default='我的博客', verbose_name='网站名称')
    site_description = models.TextField(default='欢迎访问我的博客', verbose_name='网站描述')
    site_keywords = models.CharField(max_length=200, default='博客,写作,分享', verbose_name='网站关键词')
    contact_email = models.EmailField(default='', blank=True, verbose_name='联系邮箱')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    contact_address = models.TextField(blank=True, verbose_name='联系地址')
    facebook_url = models.URLField(blank=True, verbose_name='Facebook链接')
    twitter_url = models.URLField(blank=True, verbose_name='Twitter链接')
    github_url = models.URLField(blank=True, verbose_name='GitHub链接')
    weibo_url = models.URLField(blank=True, verbose_name='微博链接')
    google_analytics_id = models.CharField(max_length=50, blank=True, verbose_name='Google Analytics ID')

    class Meta:
        verbose_name = '网站设置'
        verbose_name_plural = '网站设置'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # 确保只有一个站点设置实例
        if not self.pk and SiteSettings.objects.exists():
            raise Exception('只能有一个站点设置实例')
        super().save(*args, **kwargs)

class Tag:
    pass