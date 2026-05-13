# 域名与二级域名映射（反代 + HTTPS）

目标：把前端与后端分别映射到不同的二级域名，或者同域名下通过路径区分，并启用 HTTPS。

常见方案：
- `warehouse.example.com`：前端站点
- `api.warehouse.example.com`：后端 API

或：
- `warehouse.example.com`：前端站点
- `warehouse.example.com/api`：反代到后端

## 1) DNS 解析

在域名服务商配置：
- `warehouse` -> A 记录指向服务器公网 IP
- `api.warehouse` -> A 记录指向服务器公网 IP

等待生效后验证：

```bash
dig +short warehouse.example.com
dig +short api.warehouse.example.com
```

## 2) 反代与静态托管（Nginx 示例）

前端与后端分离子域名（推荐更清晰）：

```nginx
server {
  listen 80;
  server_name warehouse.example.com;

  root /var/www/warehouse/dist;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }
}

server {
  listen 80;
  server_name api.warehouse.example.com;

  location / {
    proxy_pass http://127.0.0.1:18808;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

同域名路径反代（前端 + `/api`）：

```nginx
server {
  listen 80;
  server_name warehouse.example.com;

  root /var/www/warehouse/dist;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://127.0.0.1:18808;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## 3) HTTPS（Let’s Encrypt / Certbot）

安装：

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

签发证书（按你的域名替换）：

```bash
sudo certbot --nginx -d warehouse.example.com -d api.warehouse.example.com
```

自动续期检查：

```bash
sudo certbot renew --dry-run
```

## 4) 前端 API 地址配置

前端通过环境变量指定后端地址：
- 本地开发默认 `http://127.0.0.1:18808`
- 生产可设置为 `https://api.warehouse.example.com` 或同域名路径方案的 `https://warehouse.example.com`

如果用子域名方案，推荐：

```bash
VUE_APP_API_BASE_URL=https://api.warehouse.example.com
```

