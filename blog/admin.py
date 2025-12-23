# blog/admin.py
from django.contrib import admin
from .models import Category, Article

class CategoryAdmin(admin.ModelAdmin):
    """分类管理"""
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

class ArticleAdmin(admin.ModelAdmin):
    """文章管理"""
    list_display = ['title', 'author', 'category', 'status', 'created_at', 'view_count']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'slug', 'author', 'category', 'status')
        }),
        ('内容', {
            'fields': ('excerpt', 'content', 'featured_image')
        }),
        ('其他信息', {
            'fields': ('is_featured', 'view_count')
        }),
    )

admin.site.register(Category, CategoryAdmin)
admin.site.register(Article, ArticleAdmin)