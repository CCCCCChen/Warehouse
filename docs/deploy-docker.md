# Docker 部署（2C2G 轻量服务器）

目标：后端 FastAPI 提供 API；前端 Vue 构建为静态文件并由 Nginx 提供；Nginx 同时反代 `/api` 到后端。

## 资源评估（2C2G）

- 可行：SQLite + FastAPI + 轻量前端静态站点对 2C2G 足够。
- 建议：关闭不必要的日志、限制 Uvicorn worker 数量（通常 1-2），并开启 Nginx gzip。
- 注意：SQLite 适合家庭/小团队与轻并发场景；高并发写入会成为瓶颈。

## 方式 A：推荐（Dockerfile + docker compose）

部署结构：
- `backend`：Python 运行 FastAPI（18808）
- `web`：Nginx（80/443），提供前端静态文件并反代 `/api`

### 1) 服务器准备

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

### 2) 在仓库根目录新增 Dockerfile（示例）

后端 Dockerfile（示例：`Dockerfile.backend`）：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app /app/app
ENV PYTHONUNBUFFERED=1
EXPOSE 18808
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18808"]
```

前端 + Nginx Dockerfile（示例：`Dockerfile.web`）：

```dockerfile
FROM node:20-alpine AS build
WORKDIR /web
COPY vue/package.json vue/package-lock.json /web/
RUN npm ci
COPY vue /web
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

Nginx 配置（示例：`nginx.conf`）：

```nginx
server {
  listen 80;
  server_name _;

  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://backend:18808;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### 3) docker compose（示例：`docker-compose.yml`）

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    restart: unless-stopped
    environment:
      - ARK_API_KEY=${ARK_API_KEY}
      - ARK_BASE_URL=${ARK_BASE_URL}
      - ARK_MODEL=${ARK_MODEL}
    volumes:
      - ./data:/app/data
    ports:
      - "18808:18808"

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "80:80"
```

### 4) 启动

```bash
docker compose up -d --build
docker compose logs -f --tail=200
```

- 前端：`http://服务器IP/`
- 后端 API 文档：`http://服务器IP:18808/docs`

## 方式 B：最少改动（仅用 Docker 运行后端）

如果暂时不想把前端打包进容器，可以只把后端容器化，前端用本地构建后上传 `dist`，用任意静态服务器（Nginx/Caddy）托管，并把 `/api` 反代到后端即可。

