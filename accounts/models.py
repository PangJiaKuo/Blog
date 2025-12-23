# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """自定义用户模型"""
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        default='profile_pics/default.jpg',
        blank=True
    )
    website = models.URLField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    facebook = models.URLField(max_length=200, blank=True)
    twitter = models.URLField(max_length=200, blank=True)
    github = models.URLField(max_length=200, blank=True)
    linkedin = models.URLField(max_length=200, blank=True)

    # 添加用户名字段的默认值（因为我们将使用 email 作为主要标识）
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    # 指定自定义管理器
    objects = CustomUserManager()

    # 修改 USERNAME_FIELD 为 email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # 添加 username 到必填字段

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'username': self.username})


class UserProfile(models.Model):
    """用户个性化设置"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('blue', 'Blue'),
            ('green', 'Green'),
        ],
        default='light'
    )
    blog_title = models.CharField(max_length=200, default='My Blog')
    blog_description = models.TextField(blank=True)
    background_image = models.ImageField(
        upload_to='blog_backgrounds/',
        blank=True,
        null=True
    )
    show_email = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    allow_guest_comments = models.BooleanField(default=False)
    posts_per_page = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.user.username}'s Profile"
