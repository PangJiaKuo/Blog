# blog/search_indexes.py
from haystack import indexes
from .models import Article  # 导入你的博客文章模型

class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    # 定义搜索字段（text是默认的全文搜索字段）
    text = indexes.CharField(document=True, use_template=True)
    # 可以添加其他要索引的字段（比如标题、内容）
    title = indexes.CharField(model_attr='title')
    content = indexes.CharField(model_attr='content')

    def get_model(self):
        # 指定要索引的模型
        return Article

    def index_queryset(self, using=None):
        # 返回要索引的对象集合（这里是所有已发布的文章）
        return self.get_model().objects.all()