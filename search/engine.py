# search/engine.py
from haystack import indexes
from blog.models import Article
from taggit.models import Tag


class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    """文章搜索索引"""
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    content = indexes.CharField(model_attr='content')
    excerpt = indexes.CharField(model_attr='excerpt')
    author = indexes.CharField(model_attr='author__username')
    category = indexes.CharField(model_attr='category__name')
    tags = indexes.MultiValueField()
    created_at = indexes.DateTimeField(model_attr='created_at')
    status = indexes.CharField(model_attr='status')

    def get_model(self):
        return Article

    def index_queryset(self, using=None):
        """只索引已发布的文章"""
        return self.get_model().objects.filter(status='published')

    def prepare_tags(self, obj):
        """准备标签字段"""
        return [tag.name for tag in obj.tags.all()]

    def prepare(self, obj):
        """准备数据"""
        data = super().prepare(obj)

        # 增加权重
        data['boost'] = 1.0
        if obj.is_featured:
            data['boost'] = 2.0

        return data


class TagIndex(indexes.SearchIndex, indexes.Indexable):
    """标签搜索索引"""
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(model_attr='description', null=True)

    def get_model(self):
        return Tag

    def index_queryset(self, using=None):
        return self.get_model().objects.all()