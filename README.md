# 个人智能知识库

![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat-square&logo=vue.js)
![Django](https://img.shields.io/badge/Django-4.x-092E20?style=flat-square&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791?style=flat-square&logo=postgresql)
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?style=flat-square)

个人智能知识库是一个结合AI大模型的个人知识管理系统，支持通过聊天获取知识并自动提取、分类和组织知识点。用户可以通过聊天窗口询问大模型，系统会自动分析对话内容，提取知识点并按层级结构进行分类整理。

## 功能特点

- 🤖 **AI对话界面**：与大模型进行自然对话
- 🧠 **自动知识提取**：从对话中提取关键知识点
- 🗂️ **智能分类标签**：自动为知识点添加分类和标签
- 🔍 **全文搜索**：快速查找已存储的知识
- 📊 **知识可视化**：树形结构展示知识层级
- 📝 **知识点编辑**：支持手动编辑和修正知识点

## 系统要求

### 后端
- Python 3.8+
- PostgreSQL 13+
- WSL或Linux环境(推荐用于运行Celery)

### 前端
- Node.js 18.19.0+
- npm 10.2.3+

## 后端安装配置

### 1. 创建项目目录
```bash
mkdir -p knowledge_hub
cd knowledge_hub
```

### 2. 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境(Windows)
venv\Scripts\activate

# 激活虚拟环境(Linux/WSL)
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install django djangorestframework django-cors-headers python-dotenv celery openai psycopg2-binary
```

### 4. PostgreSQL配置
```bash
# 在WSL中安装PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# 启动PostgreSQL服务
sudo service postgresql start

# 创建数据库和用户
sudo -u postgres psql -c "CREATE USER knowledge_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE knowledge_db OWNER knowledge_user;"
sudo -u postgres psql -c "ALTER ROLE knowledge_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE knowledge_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE knowledge_user SET timezone TO 'UTC';"
```

### 5. 环境变量配置
创建`.env`文件并添加以下内容：
```
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://knowledge_user:your_password@localhost:5432/knowledge_db
OPENAI_API_KEY=your-openai-api-key
```

生成Django秘钥：
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. 创建超级用户
```bash
python manage.py createsuperuser
```

### 8. Celery配置(使用Redis作为消息代理)
```bash
# 安装Redis(WSL/Linux)
sudo apt install redis-server

# 启动Redis
sudo service redis-server start

# 安装Celery的Redis依赖
pip install redis
```

## 前端安装配置

### 1. 创建前端项目
```bash
# 进入项目根目录
cd knowledge_hub

# 创建Vue项目
npm create vue@latest knowledge-hub-frontend

# 选择配置:
# ✓ Add TypeScript? No
# ✓ Add JSX Support? No
# ✓ Add Vue Router? Yes
# ✓ Add Pinia? Yes
# ✓ Add ESLint? Yes
# ✓ Add Prettier? Yes
```

### 2. 安装依赖
```bash
# 进入前端项目目录
cd knowledge-hub-frontend

# 安装项目依赖
npm install

# 安装额外的UI库和工具
npm install axios element-plus @element-plus/icons-vue 
npm install markdown-it highlight.js
```

### 3. 配置API地址
创建`.env.local`文件，添加以下内容：
```
VITE_API_URL=http://localhost:8000/api
```

### 4. 配置tsconfig.json
如果IDE有类型定义冲突，请确保项目根目录有如下配置：
```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "esnext",
    "moduleResolution": "node",
    "strict": true,
    "jsx": "preserve",
    "sourceMap": true,
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "lib": ["esnext", "dom"],
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "exclude": ["node_modules"]
}
```

## 启动项目

### 启动后端
```bash
# 激活虚拟环境
source venv/bin/activate # 或 venv\Scripts\activate (Windows)

# 运行开发服务器
python manage.py runserver

# 在单独的终端启动Celery工作进程(WSL/Linux下推荐)
celery -A knowledge_hub worker --loglevel=info

# Windows下推荐使用以下配置运行Celery
# 在settings.py中添加
# CELERY_TASK_ALWAYS_EAGER = True
```

### 启动前端
```bash
# 进入前端项目目录
cd knowledge-hub-frontend

# 运行开发服务器
npm run dev
```

## 访问应用
- 后端API: http://localhost:8000/api/
- 后端管理界面: http://localhost:8000/admin/
- 前端应用: http://localhost:5173/

## 项目架构

### 后端
- Django REST Framework提供API
- PostgreSQL存储结构化数据
- Celery处理异步任务(知识提取)
- OpenAI API用于对话和知识分析

### 前端
- Vue 3框架
- Vue Router管理路由
- Pinia管理状态
- Element Plus UI组件库
- Markdown-it用于渲染知识内容

## 常见问题

### PostgreSQL相关
1. 如果WSL中的PostgreSQL无法启动:
```bash
sudo service postgresql restart
```

2. 从外部(Windows)访问WSL中的PostgreSQL:
```bash
# 在WSL中查看IP地址
ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'

# 配置允许远程连接
sudo nano /etc/postgresql/13/main/postgresql.conf
# 修改: listen_addresses = '*'

sudo nano /etc/postgresql/13/main/pg_hba.conf
# 添加: host all all 0.0.0.0/0 md5

# 重启服务
sudo service postgresql restart
```

### Celery相关
Windows环境下运行Celery的问题:
```python
# settings.py中添加
CELERY_TASK_ALWAYS_EAGER = True  # 同步执行任务
CELERY_WORKER_CONCURRENCY = 1    # 单进程模式
```

### 类型检查错误
如果IDE显示Vue类型定义冲突:
1. 在VS Code设置中添加: `"vue.typescript.check.mode": "off"`
2. 或重启IDE和Vue语言服务器

## 许可证

Apache2

## 贡献

欢迎贡献代码、报告问题或提出改进建议！请先fork本仓库并创建pull request。

## 联系方式

如有任何问题，请通过issues联系我们。