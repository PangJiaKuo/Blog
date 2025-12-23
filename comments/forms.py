# comments/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Comment
from captcha.fields import CaptchaField


class CommentForm(forms.ModelForm):
    """评论表单"""
    captcha = CaptchaField(label=_('验证码'), required=False)

    class Meta:
        model = Comment
        fields = ['content', 'guest_name', 'guest_email', 'guest_website']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('写下你的评论...'),
                'class': 'form-control'
            }),
            'guest_name': forms.TextInput(attrs={
                'placeholder': _('昵称（必填）'),
                'class': 'form-control'
            }),
            'guest_email': forms.EmailInput(attrs={
                'placeholder': _('邮箱（必填）'),
                'class': 'form-control'
            }),
            'guest_website': forms.URLInput(attrs={
                'placeholder': _('网站（可选）'),
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.article = kwargs.pop('article', None)
        self.parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)

        # 如果用户已登录，隐藏游客字段
        if self.request and self.request.user.is_authenticated:
            self.fields.pop('guest_name')
            self.fields.pop('guest_email')
            self.fields.pop('guest_website')
            self.fields.pop('captcha')
        else:
            # 设置游客字段为必填
            self.fields['guest_name'].required = True
            self.fields['guest_email'].required = True

    def clean(self):
        cleaned_data = super().clean()

        # 检查评论频率限制
        if self.request:
            from datetime import timedelta
            from django.utils import timezone

            user_ip = self.request.META.get('REMOTE_ADDR')
            one_minute_ago = timezone.now() - timedelta(minutes=1)

            recent_comments = Comment.objects.filter(
                user_ip=user_ip,
                created_at__gte=one_minute_ago
            ).count()

            if recent_comments >= 3:
                raise forms.ValidationError(
                    _('评论过于频繁，请稍后再试。')
                )

        return cleaned_data

    def save(self, commit=True):
        comment = super().save(commit=False)

        if self.request:
            # 设置用户信息
            if self.request.user.is_authenticated:
                comment.author = self.request.user

            # 设置IP和用户代理
            comment.user_ip = self.request.META.get('REMOTE_ADDR')
            comment.user_agent = self.request.META.get('HTTP_USER_AGENT', '')

        # 设置文章和父评论
        if self.article:
            comment.article = self.article
        if self.parent:
            comment.parent = self.parent

        if commit:
            comment.save()

        return comment