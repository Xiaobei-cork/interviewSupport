# 面试助手 (Interview Assistant)

帮助用户记录、分析、管理面试经历和简历，结合 AI 提供智能优化建议。

## 技术栈

- **前端**：Vue 3 + Element Plus + Vite + TypeScript + Pinia
- **后端**：FastAPI + [Peewee](https://github.com/coleifer/peewee) + [peewee-async](https://github.com/tortoise/peewee-async) 2.0（异步 MySQL）
- **数据库**：MySQL 8 + Redis 7
- **迁移**：Alembic（仅负责 DDL；业务 ORM 为 Peewee，不通过 SQLAlchemy 访问数据）
- **云存储**：阿里云 OSS（可选，未配置时使用本地 `backend/uploads/`）
- **AI**：DeepSeek（可选，未配置时面试/简历分析走 Mock 兜底）

## 本地启动

### 1. 启动 MySQL 与 Redis

```bash
docker compose -f docker-compose.dev.yml up -d
```

### 2. 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env     # 已复制可跳过
alembic upgrade head          # 含 message 表 source 字段等迁移
python -m scripts.seed        # 可选：写入 demo 账号与示例数据
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动时会自动对历史评论/点赞做站内消息幂等回填（需已执行 `alembic upgrade head`）。也可手动执行：

```bash
python -m scripts.backfill_messages
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 演示账号

- 账号：`demo`
- 密码：`demo123`

## 自审检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 后端测试（需 MySQL/Redis 已启动；测试库为 SQLite 内存）
cd backend && pytest tests/ -v

# 前端构建
cd frontend && npm run build
```

## 配置说明（编码时留空，按需填写）

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | MySQL 连接串，如 `mysql+pymysql://user:pass@localhost:3306/interview` |
| `REDIS_URL` | Redis 连接串 |
| `JWT_SECRET` | JWT 密钥，生产环境请更换 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key，空则 Mock AI |
| `DEEPSEEK_BASE_URL` | 默认 `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 默认 `deepseek-v4-pro`（V4 Pro） |
| `OSS_ACCESS_KEY_ID` | 阿里云 AccessKey ID |
| `OSS_ACCESS_KEY_SECRET` | 阿里云 AccessKey Secret |
| `OSS_BUCKET` | OSS Bucket 名称 |
| `OSS_ENDPOINT` | 如 `oss-cn-hangzhou.aliyuncs.com` |
| `OSS_CDN_DOMAIN` | 可选 CDN 域名 |
| `ALIYUN_ASR_APP_KEY` | 可选，语音转文字 |
| `ALIYUN_ASR_ACCESS_KEY_ID` | 可选 |
| `ALIYUN_ASR_ACCESS_KEY_SECRET` | 可选 |

## 功能模块

- **面试复盘**：新增/编辑/删除/预览、录音上传、AI 分析、对话、评分
- **简历管理**：Word/PDF 上传、预览、AI 分析、对话、导出（中文文件名预览）
- **面试分享**：公开记录流、分页、点赞/收藏/评论；支持 `/share?id=` 直达详情
- **用户中心**：注册登录、个人资料、头像、公开面试记录
- **消息中心**：评论/点赞站内通知、未读角标、历史回填

## 项目结构（简要）

```
interviewSupport/
├── backend/app/
│   ├── api/          # FastAPI 路由
│   ├── models/       # Peewee 模型
│   ├── db/           # 查询辅助（如分享流聚合）
│   ├── services/     # AI、存储、消息通知等
│   └── database.py   # peewee-async 连接与 get_db
├── backend/alembic/  # 数据库结构迁移
└── frontend/src/   # Vue 页面与组件
```

## 仓库

https://github.com/Xiaobei-cork/interviewSupport
