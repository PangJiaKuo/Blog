# blog/forms.py
from django import forms
from django.utils.text import slugify
from .models import Article, Category
from ckeditor.widgets import CKEditorWidget


class ArticleForm(forms.ModelForm):
    """文章表单"""
    content = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Article
        fields = [
            'title', 'content', 'excerpt', 'category',
            'featured_image', 'is_featured', 'status',
            'meta_title', 'meta_description', 'meta_keywords',
            'allow_comments', 'allow_sharing'
        ]
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 过滤分类
        self.fields['category'].queryset = Category.objects.filter(is_active=True)

        # 如果是编辑模式，禁用作者字段
        if self.instance.pk:
            self.fields.pop('author', None)

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            slug = slugify(self.cleaned_data.get('title', ''))
        return slug

    def save(self, commit=True):
        article = super().save(commit=False)

        # 设置作者
        if self.user and not article.author_id:
            article.author = self.user

        if commit:
            article.save()
            self.save_m2m()  # 保存多对多关系（tags）

        return article


class ArticleFilterForm(forms.Form):
    """文章筛选表单"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="所有分类"
    )
    tag = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '标签'})
    )
    year = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    month = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', '最新'),
            ('-view_count', '最热'),
            ('-like_count', '最受欢迎'),
        ],
        required=False,
        initial='-created_at'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 动态生成年份和月份选项
        from django.db.models.functions import ExtractYear, ExtractMonth
        from django.db.models import Count

        years = Article.objects.annotate(
            year=ExtractYear('created_at')
        ).values_list('year', flat=True).distinct().order_by('-year')

        months = [
            (1, '一月'), (2, '二月'), (3, '三月'), (4, '四月'),
            (5, '五月'), (6, '六月'), (7, '七月'), (8, '八月'),
            (9, '九月'), (10, '十月'), (11, '十一月'), (12, '十二月')
        ]

        self.fields['year'].choices = [('', '所有年份')] + [(y, str(y)) for y in years]
        self.fields['month'].choices = [('', '所有月份')] + list(months)