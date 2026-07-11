#!/usr/bin/env bash
# ConceptForge 后端一键部署脚本
# 适用于全新的 Ubuntu 22.04 云服务器
# 部署：FastAPI + uvicorn + Nginx + systemd (+ 可选 certbot HTTPS)
# 幂等：可安全重复执行
# 用法: sudo bash setup.sh [--domain <域名>] [--email <邮箱>] [--repo <仓库地址>] [--branch <分支>]
set -euo pipefail

############################################################
# 参数默认值
############################################################
DOMAIN=""
EMAIL=""
REPO="https://github.com/madharker/ConceptForge.git"
BRANCH="main"

############################################################
# 参数解析
############################################################
usage() {
    cat <<USAGE
用法: sudo bash setup.sh [选项]

选项:
  --domain <域名>    部署域名（可选）。提供后 Nginx server_name 将使用该域名
  --email  <邮箱>    certbot 注册邮箱（可选）。与 --domain 同时提供时申请 Let's Encrypt 证书并强制 HTTPS
  --repo   <地址>    git 仓库地址（可选，默认: $REPO）
  --branch <分支>    git 分支名（可选，默认: $BRANCH）
  -h, --help         显示此帮助信息
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain)
            [[ $# -ge 2 ]] || { echo "错误: --domain 需要一个值" >&2; exit 1; }
            DOMAIN="$2"; shift 2 ;;
        --email)
            [[ $# -ge 2 ]] || { echo "错误: --email 需要一个值" >&2; exit 1; }
            EMAIL="$2"; shift 2 ;;
        --repo)
            [[ $# -ge 2 ]] || { echo "错误: --repo 需要一个值" >&2; exit 1; }
            REPO="$2"; shift 2 ;;
        --branch)
            [[ $# -ge 2 ]] || { echo "错误: --branch 需要一个值" >&2; exit 1; }
            BRANCH="$2"; shift 2 ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            echo "错误: 未知参数: $1" >&2; usage >&2; exit 1 ;;
    esac
done

############################################################
# 路径常量
############################################################
INSTALL_DIR="/opt/conceptforge"
BACKEND_DIR="$INSTALL_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
ENV_FILE="$BACKEND_DIR/.env"
SERVICE_FILE="/etc/systemd/system/conceptforge.service"
NGINX_AVAILABLE="/etc/nginx/sites-available/conceptforge"
NGINX_ENABLED="/etc/nginx/sites-enabled/conceptforge"
NGINX_DEFAULT="/etc/nginx/sites-enabled/default"

############################################################
# 步骤 1/12: 检查 root 权限
############################################################
echo "==> 步骤 1/12: 检查 root 权限"
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
    echo "错误: 此脚本需要 root 权限运行，请使用 sudo" >&2
    exit 1
fi

############################################################
# 步骤 2/12: 安装系统依赖
############################################################
echo "==> 步骤 2/12: 安装系统依赖 (apt)"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-pip python3-venv git nginx ufw certbot python3-certbot-nginx

############################################################
# 步骤 3/12: 克隆或更新代码仓库
############################################################
echo "==> 步骤 3/12: 获取代码仓库"
if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "==> 仓库已存在，拉取最新代码: $INSTALL_DIR"
    git -C "$INSTALL_DIR" fetch origin "$BRANCH" || git -C "$INSTALL_DIR" fetch --all || true
    git -C "$INSTALL_DIR" checkout "$BRANCH" || echo "==> 警告: 切换到分支 $BRANCH 失败，保持当前分支"
    git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH" || echo "==> 警告: git pull 失败（可能存在本地改动），继续使用现有代码"
elif [[ -d "$INSTALL_DIR" ]]; then
    BACKUP="${INSTALL_DIR}.backup.$(date +%Y%m%d%H%M%S)"
    echo "==> $INSTALL_DIR 存在但非 git 仓库，备份到 $BACKUP 后重新克隆"
    mv "$INSTALL_DIR" "$BACKUP"
    git clone --branch "$BRANCH" "$REPO" "$INSTALL_DIR"
else
    echo "==> 克隆仓库: $REPO (分支: $BRANCH) -> $INSTALL_DIR"
    git clone --branch "$BRANCH" "$REPO" "$INSTALL_DIR"
fi

############################################################
# 步骤 4/12: 创建虚拟环境并安装 Python 依赖
############################################################
echo "==> 步骤 4/12: 创建虚拟环境并安装 Python 依赖"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

############################################################
# 步骤 5/12: 生成 .env 配置文件（已存在则跳过，不覆盖）
############################################################
echo "==> 步骤 5/12: 配置环境变量文件 .env"
if [[ -f "$ENV_FILE" ]]; then
    echo "==> .env 已存在，跳过创建: $ENV_FILE"
else
    cat > "$ENV_FILE" <<'EOF'
# ConceptForge 后端环境变量配置
# 请填写真实值后执行: sudo systemctl restart conceptforge
# 说明: 当 CF_LLM_API_KEY 为空时，后端自动启用 mock 模式（无需 key 即可跑通完整流程）

# OpenAI 兼容 API 的 base url，例如 https://api.openai.com/v1
CF_LLM_BASE_URL=

# API key。留空启用 mock 回退；填入后切换为真实 LLM 调用
CF_LLM_API_KEY=

# 模型名，例如 gpt-4o-mini
CF_LLM_MODEL=
EOF
    chmod 600 "$ENV_FILE"
    echo "==> 已创建 .env 模板: $ENV_FILE"
fi

############################################################
# 步骤 6/12: 写入 systemd 服务单元（覆盖写）
############################################################
echo "==> 步骤 6/12: 写入 systemd 服务单元"
cat > "$SERVICE_FILE" <<'EOF'
[Unit]
Description=ConceptForge FastAPI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/conceptforge/backend
EnvironmentFile=/opt/conceptforge/backend/.env
ExecStart=/opt/conceptforge/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
echo "==> 已写入: $SERVICE_FILE"

############################################################
# 步骤 7/12: 启动服务并设置开机自启
############################################################
echo "==> 步骤 7/12: 启动 systemd 服务"
systemctl daemon-reload
systemctl enable conceptforge
systemctl restart conceptforge

############################################################
# 步骤 8/12: 写入 Nginx 配置（覆盖写）
############################################################
echo "==> 步骤 8/12: 写入 Nginx 配置"
if [[ -n "$DOMAIN" ]]; then
    # 有域名：server_name 使用域名，监听 80；证书由 certbot 后续注入并强制 HTTPS
    cat > "$NGINX_AVAILABLE" <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
else
    # 无域名：HTTP-only，default_server 直接用 IP 访问
    cat > "$NGINX_AVAILABLE" <<'EOF'
server {
    listen 80 default_server;
    server_name _;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
fi
echo "==> 已写入: $NGINX_AVAILABLE"

############################################################
# 步骤 9/12: 启用站点并重载 Nginx
############################################################
echo "==> 步骤 9/12: 启用 Nginx 站点并重载"
ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
rm -f "$NGINX_DEFAULT"
nginx -t
systemctl reload nginx || systemctl restart nginx

############################################################
# 步骤 10/12: 配置防火墙 (UFW)
############################################################
echo "==> 步骤 10/12: 配置防火墙 (UFW)"
ufw allow 22/tcp || true
ufw allow 80/tcp || true
if [[ -n "$DOMAIN" ]]; then
    ufw allow 443/tcp || true
fi
ufw --force enable

############################################################
# 步骤 11/12: 申请 Let's Encrypt 证书（仅在同时提供 --domain 和 --email 时）
############################################################
echo "==> 步骤 11/12: 处理 HTTPS 证书"
if [[ -n "$DOMAIN" && -n "$EMAIL" ]]; then
    echo "==> 申请 Let's Encrypt 证书并强制 HTTPS: $DOMAIN"
    certbot --nginx -d "$DOMAIN" -m "$EMAIL" --non-interactive --agree-tos --redirect
elif [[ -n "$DOMAIN" ]]; then
    echo "==> 已提供 --domain 但未提供 --email，跳过证书申请（HTTP-only）。如需 HTTPS 请加 --email 重新运行"
else
    echo "==> 未提供 --domain，跳过证书申请（HTTP-only 部署）"
fi

############################################################
# 步骤 12/12: 部署完成，输出测试信息
############################################################
echo "==> 步骤 12/12: 部署完成"
# 获取服务器公网 IP（用于无域名场景的提示），失败则回退到内网 IP，再失败回退到 127.0.0.1
PUBLIC_IP="$(curl -fsS --max-time 5 https://ifconfig.me 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo 127.0.0.1)"

echo ""
echo "============================================================"
echo "  ConceptForge 后端部署完成"
echo "============================================================"
if [[ -n "$DOMAIN" && -n "$EMAIL" ]]; then
    echo "  健康检查: curl https://$DOMAIN/api/health"
elif [[ -n "$DOMAIN" ]]; then
    echo "  健康检查: curl http://$DOMAIN/api/health"
    echo "  提示: 如需 HTTPS，请重新运行本脚本并附加 --email <你的邮箱>"
else
    echo "  健康检查: curl http://$PUBLIC_IP/api/health"
fi
echo ""
echo "  重要: 请编辑 $ENV_FILE 填入 LLM API key，然后执行:"
echo "    sudo systemctl restart conceptforge"
echo "  （未填 key 时后端将以 mock 模式运行，仍可跑通完整流程）"
echo "============================================================"
