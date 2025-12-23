# api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from blog.models import Article, Category
from comments.models import Comment
from taggit.models import Tag

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    articles_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'profile_picture', 'website', 'location',
            'date_of_birth', 'articles_count', 'date_joined'
        ]
        read_only_fields = ['date_joined']

    def get_articles_count(self, obj):
        return obj.articles.filter(status='published').count()


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""
    articles_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description',
                  'articles_count', 'created_at']

    def get_articles_count(self, obj):
        return obj.articles.filter(status='published').count()


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    articles_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'articles_count']

    def get_articles_count(self, obj):
        return obj.taggit_taggeditem_items.count()


class ArticleSerializer(serializers.ModelSerializer):
    """文章序列化器"""
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'author', 'content',
            'excerpt', 'category', 'tags', 'featured_image',
            'is_featured', 'view_count', 'like_count', 'comment_count',
            'reading_time', 'status', 'created_at', 'updated_at',
            'published_at', 'meta_title', 'meta_description',
            'meta_keywords', 'allow_comments', 'allow_sharing'
        ]
        read_only_fields = [
            'view_count', 'like_count', 'comment_count',
            'created_at', 'updated_at', 'published_at'
        ]


class ArticleCreateSerializer(serializers.ModelSerializer):
    """文章创建序列化器"""
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Article
        fields = [
            'title', 'content', 'excerpt', 'category',
            'tags', 'featured_image', 'is_featured', 'status',
            'meta_title', 'meta_description', 'meta_keywords',
            'allow_comments', 'allow_sharing'
        ]

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        request = self.context.get('request')

        article = Article.objects.create(
            author=request.user,
            **validated_data
        )

        # 添加标签
        if tags:
            article.tags.add(*tags)

        return article


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    author = UserSerializer(read_only=True)
    article = serializers.PrimaryKeyRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'article', 'author', 'parent', 'content',
            'is_approved', 'is_spam', 'is_pinned', 'guest_name',
            'guest_email', 'guest_website', 'like_count', 'reply_count',
            'created_at', 'updated_at', 'replies', 'is_owner'
        ]
        read_only_fields = [
            'like_count', 'reply_count', 'created_at', 'updated_at'
        ]

    def get_replies(self, obj):
        """获取回复"""
        if hasattr(obj, 'replies_cache'):
            replies = obj.replies_cache
        else:
            replies = obj.replies.filter(is_approved=True)

        return CommentSerializer(replies, many=True).data

    def get_is_owner(self, obj):
        """检查当前用户是否是评论作者"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False

    def create(self, validated_data):
        request = self.context.get('request')

        # 设置作者
        if request.user.is_authenticated:
            validated_data['author'] = request.user

        # 设置用户信息
        validated_data['user_ip'] = request.META.get('REMOTE_ADDR')
        validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        return super().create(validated_data)