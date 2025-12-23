# search/views.py
from typing import Any

from django.shortcuts import render
from django.core.paginator import Paginator, Page
from django.db.models import Q
from blog.models import Article, Category
from taggit.models import Tag  # 如果安装了 django-taggit


def search(request):
    """搜索视图 - 简化版"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'articles')  # articles, tags
    page = request.GET.get('page', 1)

    context = {
        'query': query,
        'search_type': search_type,
        'results': [],
        'total_results': 0,
    }

    if query:
        if search_type == 'articles':
            # 文章搜索 - 使用普通查询而不是 Haystack
            articles = Article.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query),
                status='published'
            ).select_related('author', 'category')

            # 分页
            paginator = Paginator(articles, 10)
            page_obj = paginator.get_page(page)

            context['results'] = page_obj
            context['total_results'] = articles.count()
            context['is_paginated'] = paginator.num_pages > 1

        elif search_type == 'tags':
            # 标签搜索
            tags = Tag.objects.filter(
                Q(name__icontains=query)
            ).distinct()

            # 分页
            paginator = Paginator(tags, 20)
            page_obj = paginator.get_page(page)

            context['results'] = page_obj
            context['total_results'] = tags.count()
            context['is_paginated'] = paginator.num_pages > 1

        else:
            # 综合搜索
            articles = Article.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query),
                status='published'
            ).select_related('author', 'category')[:5]

            tags = Tag.objects.filter(
                Q(name__icontains=query)
            ).distinct()[:10]

            categories = Category.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )[:5]

            context['article_results'] = articles
            context['tag_results'] = tags
            context['category_results'] = categories
            context['total_results'] = (
                    articles.count() +
                    tags.count() +
                    categories.count()
            )

    return render(request, 'search/results.html', context)


def advanced_search(request):
    """高级搜索 - 简化版"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    tag = request.GET.get('tag', '')
    author = request.GET.get('author', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    sort_by = request.GET.get('sort_by', '-created_at')
    page = request.GET.get('page', 1)

    # 构建查询
    articles = Article.objects.filter(status='published')

    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        )

    if category:
        articles = articles.filter(category__slug=category)

    if tag:
        articles = articles.filter(tags__name__icontains=tag)

    if author:
        articles = articles.filter(author__username__icontains=author)

    if start_date:
        articles = articles.filter(created_at__gte=start_date)

    if end_date:
        articles = articles.filter(created_at__lte=end_date)

    # 排序选项 - 简化，只保留支持的字段
    sort_options = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'popular': '-view_count',
        # 如果模型没有这些字段，注释掉
        # 'liked': '-like_count',
        'commented': '-comment_count',
    }

    articles = articles.order_by(sort_options.get(sort_by, '-created_at'))

    # 分页
    paginator = Paginator(articles, 15)
    page_obj = paginator.get_page(page)

    # 获取分类和标签用于筛选
    categories = Category.objects.all()  # 移除 is_active 过滤
    tags = Tag.objects.all()[:20]

    context = {
        'results': page_obj,
        'query': query,
        'category': category,
        'tag': tag,
        'author': author,
        'start_date': start_date,
        'end_date': end_date,
        'sort_by': sort_by,
        'categories': categories,
        'tags': tags,
        'total_results': articles.count(),
        'is_paginated': paginator.num_pages > 1,
    }

    return render(request, 'search/results.html', context)
