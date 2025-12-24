# blog/migrations/0005_add_programming_categories.py
from django.db import migrations


def add_programming_categories(apps, schema_editor):
    """添加编程相关分类"""
    category = apps.get_model('blog', 'Category')

    # 只添加 Python、C++、Java、Django 这四个编程分类
    programming_categories = [
        ('python', 'Python', 'Python编程语言相关文章'),
        ('cpp', 'C++', 'C++编程语言相关文章'),
        ('java', 'Java', 'Java编程语言相关文章'),
        ('django', 'Django', 'Django框架相关文章'),
        ('other','other','other'),
    ]

    for order, (slug, name, description) in enumerate(programming_categories, start=1):
        category.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'is_active': True,
                'order': order
            }
        )

    print(f"✅ 成功添加编程分类：{', '.join([name for _, name, _ in programming_categories])}")


class Migration(migrations.Migration):
    # 注意：这里指向您的上一个迁移文件 0004
    dependencies = [
        ('blog', '0003_alter_article_category'),
    ]

    operations = [
        migrations.RunPython(add_programming_categories),
    ]
