# 面试助手 (Interview Assistant)

帮助用户记录、分析、管理面试经历和简历，结合 AI 提供智能优化建议。

## 技术栈

- 前端：Vue 3 + Element Plus + Vite + TypeScript
- 后端：FastAPI + SQLAlchemy
- 数据库：MySQL 8 + Redis 7
- 云存储：阿里云 OSS（可选，未配置时使用本地存储）
- AI：DeepSeek（可选，未配置时使用 Mock 模式）

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
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

# 后端测试（需 MySQL/Redis 已启动）
cd backend && pytest tests/ -v

# 前端构建
cd frontend && npm run build
```

## 配置说明（编码时留空，按需填写）

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | MySQL 连接串 |
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
- **简历管理**：Word/PDF 上传、预览、AI 分析、对话、导出
- **面试分享**：公开记录、点赞、收藏、评论
- **用户中心**：注册登录、个人资料、头像、改密
- **消息中心**：系统通知与未读角标
