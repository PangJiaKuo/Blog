# comments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from .models import Comment, CommentLike
from .forms import CommentForm
from blog.models import Article


class AddCommentView(View):
    """添加评论"""

    @method_decorator(csrf_protect)
    def post(self, request, article_slug):
        article = get_object_or_404(Article, slug=article_slug)

        # 检查是否允许评论
        if not article.allow_comments:
            return JsonResponse({
                'success': False,
                'message': '该文章已关闭评论。'
            })

        form = CommentForm(
            request.POST,
            request=request,
            article=article
        )

        if form.is_valid():
            comment = form.save()

            # 更新文章评论计数
            article.comment_count += 1
            article.save(update_fields=['comment_count'])

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '评论发布成功！',
                    'comment_id': comment.id
                })
            else:
                messages.success(request, '评论发布成功！')
                return redirect(article.get_absolute_url())

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
        else:
            messages.error(request, '评论发布失败，请检查表单。')
            return redirect(article.get_absolute_url())


class ReplyCommentView(View):
    """回复评论"""

    @method_decorator(csrf_protect)
    def post(self, request, comment_id):
        parent_comment = get_object_or_404(Comment, id=comment_id)
        article = parent_comment.article

        # 检查是否允许评论
        if not article.allow_comments:
            return JsonResponse({
                'success': False,
                'message': '该文章已关闭评论。'
            })

        form = CommentForm(
            request.POST,
            request=request,
            article=article,
            parent=parent_comment
        )

        if form.is_valid():
            comment = form.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '回复发布成功！',
                    'comment_id': comment.id
                })
            else:
                messages.success(request, '回复发布成功！')
                return redirect(article.get_absolute_url())

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
        else:
            messages.error(request, '回复发布失败，请检查表单。')
            return redirect(article.get_absolute_url())


@require_POST
@login_required
def like_comment(request, comment_id):
    """点赞评论"""
    comment = get_object_or_404(Comment, id=comment_id)

    like, created = CommentLike.objects.get_or_create(
        comment=comment,
        user=request.user
    )

    if not created:
        like.delete()
        liked = False
    else:
        comment.like_count += 1
        comment.save(update_fields=['like_count'])
        liked = True

    return JsonResponse({
        'liked': liked,
        'likes_count': comment.like_count
    })


@login_required
def delete_comment(request, comment_id):
    """删除评论"""
    comment = get_object_or_404(Comment, id=comment_id)

    # 检查权限
    if not (request.user == comment.author or request.user.is_staff):
        messages.error(request, '您没有权限删除此评论。')
        return redirect(comment.article.get_absolute_url())

    article = comment.article

    # 如果是父评论，同时删除所有回复
    if comment.replies.exists():
        comment.replies.all().delete()

    comment.delete()

    # 更新文章评论计数
    article.comment_count = max(0, article.comment_count - 1)
    article.save(update_fields=['comment_count'])

    messages.success(request, '评论已删除。')
    return redirect(article.get_absolute_url())


@login_required
def pin_comment(request, comment_id):
    """置顶评论"""
    comment = get_object_or_404(Comment, id=comment_id)

    # 检查权限
    if not (request.user == comment.article.author or request.user.is_staff):
        messages.error(request, '您没有权限置顶此评论。')
        return redirect(comment.article.get_absolute_url())

    comment.is_pinned = not comment.is_pinned
    comment.save(update_fields=['is_pinned'])

    action = '置顶' if comment.is_pinned else '取消置顶'
    messages.success(request, f'评论已{action}。')
    return redirect(comment.article.get_absolute_url())