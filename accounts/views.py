# accounts/views.py
import traceback

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count
from .models import CustomUser, UserProfile,CaptchaModel
from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileForm, PasswordChangeForm
from blog.models import Article
from django.contrib.auth import logout as auth_logout
from django.http.response import JsonResponse
from django.core.mail import send_mail
import random
import string
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache


# class RegisterView(CreateView):
#     """用户注册视图"""
#     form_class = CustomUserCreationForm
#     template_name = 'accounts/register.html'
#     success_url = reverse_lazy('blog:home')
#
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         # 自动登录
#         login(self.request, self.object)
#         # 创建用户配置
#         UserProfile.objects.create(user=self.object)
#         messages.success(self.request, '注册成功！欢迎来到博客平台。')
#         return response

@require_http_methods(['GET', 'POST'])
def RegisterView(request):
    if request.method == 'GET':
        return render(request, 'accounts/register.html')
    else:
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            User.objects.create_user(email=email, username=username, password=password)
            return redirect(reverse('accounts:login'))
        else:
            print(form.errors)
            # 重新跳转到登录页面
            return redirect(reverse('accounts:register'))
            # return render(request, 'register.html', context={"form": form})


def send_email_captcha(request):
    # 检查是否为AJAX POST请求
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST' and is_ajax:
        email = request.POST.get('email', '').strip().lower()
        if not email:
            return JsonResponse({'status': 'error', 'msg': '请输入邮箱地址'})

        # 生成6位验证码
        captcha = ''.join(random.choices(string.digits, k=6))
        # 存储到Session，有效期10分钟
        request.session[f'email_captcha_{email}'] = captcha
        request.session.set_expiry(600)  # 600秒=10分钟

        # 发送邮件
        try:
            send_mail(
                subject='【你的网站】注册验证码',
                message=f'你的注册验证码是：{captcha}，有效期10分钟，请勿泄露给他人。',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success', 'msg': '验证码已发送至你的邮箱，请查收'})
        except Exception as e:
            print("邮件发送错误：", traceback.format_exc())
            return JsonResponse({'status': 'error', 'msg': f'邮件发送失败：{str(e)}'})
    return JsonResponse({'status': 'error', 'msg': '请求方式错误'})


# 注册视图（传递request给表单）
def register(request):
    if request.method == 'POST':
        # 关键：把request传给表单，用于读取Session
        form = CustomUserCreationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            messages.success(request, '注册成功！请登录')
            return redirect('accounts:login')  # 确保login路由命名空间正确
    else:
        form = CustomUserCreationForm(request=request)

    return render(request, 'accounts/register.html', {'form': form})

class ProfileView(DetailView):
    """用户资料页面"""
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'

    def get_object(self):
        return get_object_or_404(
            CustomUser,
            username=self.kwargs['username']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        articles = Article.objects.filter(
            author=user,
            status='published'
        ).select_related('category').prefetch_related('tags')

        context['articles'] = articles
        context['article_count'] = articles.count()
        context['is_owner'] = self.request.user == user
        return context


@method_decorator(csrf_protect, name='dispatch')
class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """资料更新视图"""
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile_edit.html'
    slug_field = 'username'  # 指定使用哪个字段作为slug
    slug_url_kwarg = 'username'  # 指定URL参数名

    def get_object(self, queryset=None):
        """重写get_object方法，使用username查找用户"""
        username = self.kwargs.get('username')
        return get_object_or_404(CustomUser, username=username)

    def test_func(self):
        user = self.get_object()
        return self.request.user == user

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.object.username})

    def form_valid(self, form):
        messages.success(self.request, '个人资料已更新！')
        return super().form_valid(form)


@login_required
def profile_settings(request):
    """用户设置页面"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '设置已保存！')
            return redirect('accounts:settings')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/settings.html', {'form': form})


@login_required
def change_password(request):
    """修改密码"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, '密码修改成功！')
            return redirect('accounts:profile', username=user.username)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def user_dashboard(request):
    """用户仪表板"""
    user = request.user
    articles = Article.objects.filter(author=user)
    published_count = articles.filter(status='published').count()
    draft_count = articles.filter(status='draft').count()

    context = {
        'total_articles': articles.count(),
        'published_count': published_count,
        'draft_count': draft_count,
        'recent_articles': articles.order_by('-created_at')[:5],
        'popular_articles': articles.order_by('-view_count')[:5],
    }

    return render(request, 'accounts/dashboard.html', context)

@login_required
def logout(request):
    # 执行退出登录操作
    auth_logout(request)
    # 重定向到登录页面
    return redirect('accounts:login')  # 修改这里
