# blog/views.py
import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView,
    UpdateView, DeleteView, TemplateView
)
from django.views import View
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from .models import Article, Category, ArticleLike, ArticleBookmark
from .forms import ArticleForm, ArticleFilterForm


class HomeView(ListView):
    """首页视图"""
    model = Article
    template_name = 'blog/home.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        queryset = Article.objects.filter(
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')

        # 应用筛选
        form = ArticleFilterForm(self.request.GET)
        if form.is_valid():
            category = form.cleaned_data.get('category')
            tag = form.cleaned_data.get('tag')
            year = form.cleaned_data.get('year')
            month = form.cleaned_data.get('month')
            sort = form.cleaned_data.get('sort', '-created_at')  # 有默认值

            if category:
                queryset = queryset.filter(category=category)
            if tag:
                queryset = queryset.filter(tags__name__icontains=tag)
            if year:
                queryset = queryset.filter(created_at__year=year)
            if month:
                queryset = queryset.filter(created_at__month=month)

            # ✅ 确保sort不是空字符串
            if sort and sort.strip():  # 检查sort是否非空
                queryset = queryset.order_by(sort)
            else:
                queryset = queryset.order_by('-created_at')  # 默认排序

        # ✅ 如果没有表单验证或者排序失败，确保有默认排序
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 热门文章
        context['popular_articles'] = cache.get('popular_articles')
        if not context['popular_articles']:
            context['popular_articles'] = Article.objects.filter(
                status='published'
            ).order_by('-view_count')[:5]
            cache.set('popular_articles', context['popular_articles'], 3600)

        # 推荐文章
        context['featured_articles'] = Article.objects.filter(
            status='published',
            is_featured=True
        ).order_by('-created_at')[:3]

        # 最新评论
        from comments.models import Comment
        context['recent_comments'] = Comment.objects.filter(
            is_approved=True
        ).select_related('author', 'article').order_by('-created_at')[:5]

        # 分类统计
        context['categories'] = Category.objects.filter(
            is_active=True
        ).annotate(
            article_count=Count('articles')
        ).filter(article_count__gt=0).order_by('-article_count')[:10]

        # 标签云
        from taggit.models import Tag
        context['tags'] = Tag.objects.annotate(
            num_times=Count('taggit_taggeditem_items')
        ).order_by('-num_times')[:20]

        context['filter_form'] = ArticleFilterForm(self.request.GET)

        return context


@method_decorator(cache_page(60 * 15), name='dispatch')
@method_decorator(vary_on_cookie, name='dispatch')
class ArticleDetailView(DetailView):
    """文章详情视图"""
    model = Article
    template_name = 'blog/article_detail.html'
    context_object_name = 'article'

    def get_object(self):
        obj = super().get_object()

        # 增加浏览量（排除作者自己）
        if self.request.user != obj.author:
            Article.objects.filter(id=obj.id).update(
                view_count=F('view_count') + 1
            )
            obj.view_count += 1  # 更新本地对象

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        # 检查用户是否点赞或收藏
        if self.request.user.is_authenticated:
            context['has_liked'] = ArticleLike.objects.filter(
                article=article,
                user=self.request.user
            ).exists()
            context['has_bookmarked'] = ArticleBookmark.objects.filter(
                article=article,
                user=self.request.user
            ).exists()

        # 相关文章（基于分类）
        context['related_articles'] = Article.objects.filter(
            category=article.category,
            status='published'
        ).exclude(id=article.id).order_by('-created_at')[:3]

        # 上一篇和下一篇文章
        context['prev_article'] = Article.objects.filter(
            status='published',
            created_at__lt=article.created_at
        ).order_by('-created_at').first()

        context['next_article'] = Article.objects.filter(
            status='published',
            created_at__gt=article.created_at
        ).order_by('created_at').first()

        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """创建文章视图"""
    model = Article
    form_class = ArticleForm
    template_name = 'blog/article_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            '文章已保存！' if form.instance.status == 'draft' else '文章已发布！'
        )
        return response

    def get_success_url(self):
        if self.object.status == 'draft':
            return reverse_lazy('blog:draft_list')
        return self.object.get_absolute_url()


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """更新文章视图"""
    model = Article
    form_class = ArticleForm
    template_name = 'blog/article_form.html'

    def test_func(self):
        article = self.get_object()
        return self.request.user == article.author or self.request.user.is_staff

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, '文章已更新！')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除文章视图"""
    model = Article
    template_name = 'blog/article_confirm_delete.html'
    success_url = reverse_lazy('blog:home')

    def test_func(self):
        article = self.get_object()
        return self.request.user == article.author or self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(request, '文章已删除！')
        return super().delete(request, *args, **kwargs)


class LikeArticleView(LoginRequiredMixin, View):
    """点赞文章"""

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk)

        like, created = ArticleLike.objects.get_or_create(
            article=article,
            user=request.user
        )

        if not created:
            like.delete()
            liked = False
        else:
            article.like_count = F('like_count') + 1
            article.save(update_fields=['like_count'])
            liked = True

        article.refresh_from_db()

        return JsonResponse({
            'liked': liked,
            'likes_count': article.like_count
        })


class BookmarkArticleView(LoginRequiredMixin, View):
    """收藏文章"""

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk)

        bookmark, created = ArticleBookmark.objects.get_or_create(
            article=article,
            user=request.user
        )

        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True

        return JsonResponse({
            'bookmarked': bookmarked,
            'message': '已收藏' if bookmarked else '已取消收藏'
        })


class CategoryView(ListView):
    """分类视图"""
    template_name = 'blog/category.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['slug']
        )
        return Article.objects.filter(
            category=self.category,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class TagView(ListView):
    """标签视图"""
    template_name = 'blog/tag.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        from taggit.models import Tag
        self.tag = get_object_or_404(
            Tag,
            slug=self.kwargs['slug']
        )
        return Article.objects.filter(
            tags=self.tag,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        return context


class ArchiveView(ListView):
    """归档视图"""
    template_name = 'blog/archive.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        year = self.kwargs['year']
        month = self.kwargs.get('month')

        queryset = Article.objects.filter(
            created_at__year=year,
            status='published'
        )

        if month:
            queryset = queryset.filter(created_at__month=month)

        return queryset.select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['year'] = self.kwargs['year']
        context['month'] = self.kwargs.get('month')

        # 获取归档统计
        from django.db.models.functions import ExtractYear, ExtractMonth
        from django.db.models import Count

        archives = Article.objects.filter(
            status='published'
        ).annotate(
            year=ExtractYear('created_at'),
            month=ExtractMonth('created_at')
        ).values('year', 'month').annotate(
            count=Count('id')
        ).order_by('-year', '-month')

        context['archives'] = archives

        return context


class DraftListView(LoginRequiredMixin, ListView):
    """草稿列表"""
    template_name = 'blog/draft_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        return Article.objects.filter(
            author=self.request.user,
            status='draft'
        ).order_by('-updated_at')

        # 排序处理
        sort = self.request.GET.get('sort', '-updated_at')
        if sort:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = context['articles']

        # 计算总字数
        total_chars = sum(len(article.content) for article in articles)
        context['total_characters'] = total_chars

        # 计算最旧的草稿天数
        if articles:
            from django.utils.timezone import now
            oldest = min(articles, key=lambda x: x.updated_at)
            delta = now() - oldest.updated_at
            context['oldest_draft_days'] = delta.days
        else:
            context['oldest_draft_days'] = 0

        return context


class PublishDraftView(LoginRequiredMixin, View):
    """发布草稿视图"""

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk, author=request.user)

        if article.status == 'draft':
            article.status = 'published'
            article.save()
            return JsonResponse({'success': True, 'message': '草稿已发布'})

        return JsonResponse({'success': False, 'error': '文章不是草稿状态'})

class BookmarkListView(LoginRequiredMixin, ListView):
    """收藏列表"""
    template_name = 'blog/bookmark_list.html'
    context_object_name = 'bookmarks'
    paginate_by = 12

    def get_queryset(self):
        queryset = ArticleBookmark.objects.filter(
            user=self.request.user
        ).select_related(
            'article',
            'article__author',
            'article__category'
        ).order_by('-created_at')

        # 排序处理
        sort = self.request.GET.get('sort', '-created_at')
        if sort:
            queryset = queryset.order_by(sort)

        # 分类筛选
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(article__category__slug=category_slug)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 获取分类统计
        from django.db.models import Count
        categories = Category.objects.filter(
            articles__bookmarks__user=self.request.user
        ).annotate(count=Count('articles__bookmarks')).distinct()

        context['categories'] = categories
        context['categories_count'] = categories.count()

        # 计算作者数量
        authors = set(bookmark.article.author for bookmark in context['bookmarks'])
        context['total_authors'] = len(authors)

        return context


# 在 views.py 末尾添加
class PublishMultipleDraftsView(LoginRequiredMixin, View):
    """批量发布草稿"""

    def post(self, request):
        import json
        data = json.loads(request.body)
        draft_ids = data.get('draft_ids', [])

        published_count = 0
        for draft_id in draft_ids:
            try:
                article = Article.objects.get(
                    id=draft_id,
                    author=request.user,
                    status='draft'
                )
                article.status = 'published'
                article.save()
                published_count += 1
            except Article.DoesNotExist:
                continue

        return JsonResponse({
            'success': True,
            'published_count': published_count
        })


class DeleteMultipleDraftsView(LoginRequiredMixin, View):
    """批量删除草稿"""

    def post(self, request):
        import json
        data = json.loads(request.body)
        draft_ids = data.get('draft_ids', [])

        deleted_count = 0
        for draft_id in draft_ids:
            try:
                article = Article.objects.get(
                    id=draft_id,
                    author=request.user
                )
                article.delete()
                deleted_count += 1
            except Article.DoesNotExist:
                continue

        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count
        })


class RemoveMultipleBookmarksView(LoginRequiredMixin, View):
    """批量取消收藏"""

    def post(self, request):
        import json
        data = json.loads(request.body)
        bookmark_ids = data.get('bookmark_ids', [])

        removed_count = 0
        for bookmark_id in bookmark_ids:
            try:
                bookmark = ArticleBookmark.objects.get(
                    id=bookmark_id,
                    user=request.user
                )
                bookmark.delete()
                removed_count += 1
            except ArticleBookmark.DoesNotExist:
                continue

        return JsonResponse({
            'success': True,
            'removed_count': removed_count
        })