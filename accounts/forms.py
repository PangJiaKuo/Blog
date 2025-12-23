# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile, CaptchaModel
from captcha.fields import CaptchaField
from django.core.mail import send_mail
from django.conf import settings
import secrets


class CustomUserCreationForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True)
    captcha = CaptchaField(label=_('验证码'))

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('该邮箱已被注册'))
        return email

    # 添加保存方法
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False  # 新增：设置用户为未激活状态

        if commit:
            user.save()
            # 生成验证链接（最简单的方式）
            self.send_verification_email(user)

        return user

    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        email = self.cleaned_data.get('email')

        captcha_model = CaptchaModel.objects.filter(email=email, captcha=captcha).first()
        if not captcha_model:
            raise forms.ValidationError("验证码和邮箱不匹配！")
        captcha_model.delete()
        return captcha

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