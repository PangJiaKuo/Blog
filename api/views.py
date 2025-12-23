# api/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from blog.models import Article, Category, ArticleLike, ArticleBookmark
from comments.models import Comment, CommentLike
from .serializers import (
    UserSerializer, ArticleSerializer, ArticleCreateSerializer,
    CategorySerializer, CommentSerializer
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """用户API"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined']

    @action(detail=True, methods=['get'])
    def articles(self, request, pk=None):
        """获取用户的文章"""
        user = self.get_object()
        articles = Article.objects.filter(
            author=user,
            status='published'
        ).select_related('category').prefetch_related('tags')

        page = self.paginate_queryset(articles)
        serializer = ArticleSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ArticleViewSet(viewsets.ModelViewSet):
    """文章API"""
    queryset = Article.objects.filter(status='published')
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['category', 'author', 'is_featured']
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = [
        'created_at', 'updated_at', 'view_count',
        'like_count', 'comment_count'
    ]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ArticleCreateSerializer
        return ArticleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # 过滤标签
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__name=tag)

        return queryset.select_related('author', 'category').prefetch_related('tags')

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞文章"""
        article = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {'detail': '请先登录。'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        like, created = ArticleLike.objects.get_or_create(
            article=article,
            user=user
        )

        if not created:
            like.delete()
            liked = False
        else:
            article.like_count += 1
            article.save(update_fields=['like_count'])
            liked = True

        article.refresh_from_db()

        return Response({
            'liked': liked,
            'likes_count': article.like_count
        })

    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """收藏文章"""
        article = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {'detail': '请先登录。'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        bookmark, created = ArticleBookmark.objects.get_or_create(
            article=article,
            user=user
        )

        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True

        return Response({'bookmarked': bookmarked})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """获取文章评论"""
        article = self.get_object()
        comments = article.comments.filter(
            parent__isnull=True,
            is_approved=True
        ).select_related('author').prefetch_related('replies')

        # 预加载回复
        for comment in comments:
            comment.replies_cache = comment.replies.filter(is_approved=True)

        page = self.paginate_queryset(comments)
        serializer = CommentSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """分类API"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @action(detail=True, methods=['get'])
    def articles(self, request, pk=None):
        """获取分类下的文章"""
        category = self.get_object()
        articles = Article.objects.filter(
            category=category,
            status='published'
        ).select_related('author').prefetch_related('tags')

        page = self.paginate_queryset(articles)
        serializer = ArticleSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """评论API"""
    queryset = Comment.objects.filter(is_approved=True)
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # 根据文章ID过滤
        article_id = self.request.query_params.get('article')
        if article_id:
            queryset = queryset.filter(article_id=article_id)

        # 只返回顶级评论
        if self.action == 'list':
            queryset = queryset.filter(parent__isnull=True)

        return queryset.select_related('author', 'article').prefetch_related('replies')

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞评论"""
        comment = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {'detail': '请先登录。'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=user
        )

        if not created:
            like.delete()
            liked = False
        else:
            comment.like_count += 1
            comment.save(update_fields=['like_count'])
            liked = True

        return Response({
            'liked': liked,
            'likes_count': comment.like_count
        })

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """回复评论"""
        parent_comment = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 设置父评论和文章
        serializer.validated_data['parent'] = parent_comment
        serializer.validated_data['article'] = parent_comment.article

        comment = serializer.save()

        # 更新回复计数
        parent_comment.reply_count += 1
        parent_comment.save(update_fields=['reply_count'])

        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )