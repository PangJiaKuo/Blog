# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    # 文章操作
    path('create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('update/<slug:slug>/', views.ArticleUpdateView.as_view(), name='article_update'),
    path('delete/<slug:slug>/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('article/<int:pk>/publish/', views.PublishDraftView.as_view(), name='article_publish'),

    # 互动功能
    path('article/<int:pk>/like/', views.LikeArticleView.as_view(), name='article_like'),
    path('article/<int:pk>/bookmark/', views.BookmarkArticleView.as_view(), name='article_bookmark'),

    # 分类和标签
    path('tag/<slug:slug>/', views.TagView.as_view(), name='tag'),
    path('archive/<int:year>/', views.ArchiveView.as_view(), name='archive'),
    path('archive/<int:year>/<int:month>/', views.ArchiveView.as_view(), name='archive_monthly'),

    # 个人功能
    path('drafts/', views.DraftListView.as_view(), name='draft_list'),
    path('bookmarks/', views.BookmarkListView.as_view(), name='bookmark_list'),

    # 批量操作
    path('drafts/publish-multiple/', views.PublishMultipleDraftsView.as_view(), name='publish_multiple_drafts'),
    path('drafts/delete-multiple/', views.DeleteMultipleDraftsView.as_view(), name='delete_multiple_drafts'),
    path('bookmarks/remove-multiple/', views.RemoveMultipleBookmarksView.as_view(), name='remove_multiple_bookmarks'),
]