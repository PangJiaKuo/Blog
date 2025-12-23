# blog/context_processors.py
from django.conf import settings
from django.db.models import Count
from .models import Category, Article, Tag, SiteSettings
from comments.models import Comment
from datetime import datetime


def site_settings(request):
    """站点设置"""
    try:
        site_settings_obj = SiteSettings.objects.first()
    except:
        site_settings_obj = {
            'site_name': getattr(settings, 'SITE_NAME', '我的博客'),
            'site_description': getattr(settings, 'SITE_DESCRIPTION', '欢迎访问我的博客'),
            'site_keywords': getattr(settings, 'SITE_KEYWORDS', '博客,写作,分享'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', ''),
            'contact_phone': getattr(settings, 'CONTACT_PHONE', ''),
            'contact_address': getattr(settings, 'CONTACT_ADDRESS', ''),
            'facebook_url': getattr(settings, 'FACEBOOK_URL', ''),
            'twitter_url': getattr(settings, 'TWITTER_URL', ''),
            'github_url': getattr(settings, 'GITHUB_URL', ''),
            'weibo_url': getattr(settings, 'WEIBO_URL', ''),
            'google_analytics_id': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
        }

    return {
        'site_settings': site_settings_obj,
        'current_year': datetime.now().year,
    }


def navigation_categories(request):
    """导航栏分类"""
    try:
        categories = Category.objects.filter(
            is_active=True,
            show_in_nav=True
        ).annotate(
            article_count=Count('articles')
        ).filter(article_count__gt=0)[:10]
    except:
        categories = []

    return {'categories': categories}


def common_context(request):
    """所有模板共用的上下文"""
    context = {}

    # 合并所有上下文
    context.update(site_settings(request))
    context.update(navigation_categories(request))

    # 添加用户相关信息
    if request.user.is_authenticated:
        from .models import Article, ArticleBookmark
        context['draft_count'] = Article.objects.filter(
            author=request.user,
            status='draft'
        ).count()

        context['bookmark_count'] = ArticleBookmark.objects.filter(
            user=request.user
        ).count()

    return context