# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile, CaptchaModel
from captcha.fields import CaptchaField
from django.core.mail import send_mail
from django.conf import settings
import secrets
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """用户注册表单"""
    # 验证码字段
    captcha = forms.CharField(
        label='邮箱验证码',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'placeholder': '输入6位验证码'}),
        error_messages={
            'required': '请输入验证码',
            'max_length': '验证码长度为6位',
            'min_length': '验证码长度为6位'
        }
    )
    # 邮箱字段（必填）
    email = forms.EmailField(
        required=True,
        error_messages={'required': '请输入邮箱地址'}
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'captcha', 'password1', 'password2')

    # 初始化时接收request
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    # 验证验证码（从Session读取）
    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha', '').strip()
        email = self.cleaned_data.get('email', '').strip().lower()

        if not self.request:
            raise forms.ValidationError('请求异常，请刷新页面重试')
        if not email:
            raise forms.ValidationError('请先输入邮箱地址')

        # 从Session读取验证码
        real_captcha = self.request.session.get(f'email_captcha_{email}')
        if not real_captcha:
            raise forms.ValidationError('验证码已过期或未发送，请重新获取')
        if captcha != real_captcha:
            raise forms.ValidationError('验证码错误，请重新输入')

        # 验证后删除Session，防止重复使用
        del self.request.session[f'email_captcha_{email}']
        return captcha

    # 验证两次密码一致
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('两次密码输入不一致')
        return password2

    # 清洗邮箱（转小写）
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('该邮箱已被注册，请更换邮箱')
        return email
class CustomUserChangeForm(UserChangeForm):
    """用户信息修改表单"""

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'bio',
                  'profile_picture', 'website', 'location', 'date_of_birth')


class ProfileForm(forms.ModelForm):
    """个人资料表单"""

    class Meta:
        model = UserProfile
        fields = ('theme', 'blog_title', 'blog_description',
                  'background_image', 'show_email', 'allow_comments',
                  'allow_guest_comments', 'posts_per_page')
        widgets = {
            'blog_description': forms.Textarea(attrs={'rows': 3}),
        }


class PasswordChangeForm(forms.Form):
    """密码修改表单"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('旧密码')}),
        label=_('旧密码')
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('新密码')}),
        label=_('新密码')
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('确认新密码')}),
        label=_('确认新密码')
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(_('旧密码错误'))
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('两次输入的密码不一致'))

        return cleaned_data