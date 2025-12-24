# comments/urls.py 完整正确配置
from django.urls import path
from . import views

app_name = 'comments'  # 命名空间，避免 URL 名称冲突

urlpatterns = [
    # 提交评论（关联文章 slug）
    path('add/<slug:article_slug>/', views.AddCommentView.as_view(), name='add_comment'),
    # 回复评论（关联父评论 ID）
    path('reply/<int:comment_id>/', views.ReplyCommentView.as_view(), name='reply_comment'),
    # 点赞评论（关键：函数名是 like_comment，和 views.py 一致）
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    # 删除评论
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    # 置顶评论（函数名：pin_comment）
    path('comment/<int:comment_id>/pin/', views.pin_comment, name='pin_comment'),
]