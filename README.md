# 我的Django博客项目
基于Django 5.0开发的博客系统，支持文章发布、评论、搜索、用户管理等功能。

## 运行步骤
1. 克隆仓库：
   git clone https://github.com/PangJiaKuo/Blog.git
2. 创建虚拟环境：
   python -m venv venv
3. 激活虚拟环境：
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
4. 安装依赖：
   pip install -r requirements.txt
5. 创建.env文件，配置以下内容（参考示例）：
   SECRET_KEY=你的随机密钥
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_NAME=blog
   DATABASE_USER=root
   DATABASE_PASSWORD=你的数据库密码
   DATABASE_HOST=localhost
   DATABASE_PORT=3306
6. 执行数据库迁移：
   python manage.py migrate
7. 创建超级用户：
   python manage.py createsuperuser
8. 启动服务：
   python manage.py runserver
