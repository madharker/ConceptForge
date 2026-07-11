# ConceptForge 后端一键部署脚本

本目录提供 `setup.sh`，可在全新的 Ubuntu 22.04 云服务器上一键部署 ConceptForge 后端（FastAPI + uvicorn + Nginx + systemd，可选 Let's Encrypt HTTPS）。脚本幂等，可安全重复执行。

## 前置条件

- 操作系统：Ubuntu 22.04 LTS（全新服务器即可）
- 权限：root（建议使用 `sudo` 执行）
- 网络：服务器可访问公网（用于 apt 安装、git 克隆，以及可选的证书申请）
- 域名（可选）：如需 HTTPS，请先将域名 A 记录解析到服务器公网 IP，并准备好用于注册证书的邮箱
- 端口：确保 22（SSH）、80（HTTP）可访问；如使用 HTTPS 还需开放 443

## 快速开始

将本目录上传到服务器后，进入目录执行：

### 方式一：带域名 + HTTPS（推荐生产环境）

```bash
sudo bash setup.sh --domain conceptforge.example.com --email you@example.com
```

### 方式二：不带域名（HTTP-only，使用服务器 IP 访问）

```bash
sudo bash setup.sh
```

部署完成后即可用 `curl` 验证健康检查接口。

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--domain <域名>` | 否 | 无 | 部署域名。提供后 Nginx `server_name` 使用该域名；与 `--email` 同时提供时自动申请 Let's Encrypt 证书并强制 HTTPS |
| `--email <邮箱>` | 否 | 无 | certbot 注册邮箱。仅在同时提供 `--domain` 时生效 |
| `--repo <地址>` | 否 | `https://github.com/madharker/ConceptForge.git` | git 仓库地址 |
| `--branch <分支>` | 否 | `main` | 部署使用的 git 分支 |

> 说明：仅提供 `--domain` 而不提供 `--email` 时，脚本按 HTTP-only 部署（可用域名访问但不申请证书）。

## 部署后配置

脚本会在 `/opt/conceptforge/backend/.env` 生成环境变量模板（**仅在文件不存在时创建，不会覆盖已有配置**）。

1. 编辑 `.env` 文件填入 LLM 配置：

```bash
sudo nano /opt/conceptforge/backend/.env
```

需配置的变量：

| 变量 | 说明 |
| --- | --- |
| `CF_LLM_BASE_URL` | OpenAI 兼容 API 的 base url，例如 `https://api.openai.com/v1` |
| `CF_LLM_API_KEY` | API key。**留空时自动启用 mock 模式**，无需 key 即可跑通完整流程 |
| `CF_LLM_MODEL` | 模型名，例如 `gpt-4o-mini` |

2. 保存后重启服务使配置生效：

```bash
sudo systemctl restart conceptforge
```

## 常用运维命令

```bash
# 查看服务状态
sudo systemctl status conceptforge

# 查看实时日志
sudo journalctl -u conceptforge -f

# 查看最近 100 行日志
sudo journalctl -u conceptforge -n 100

# 重启服务
sudo systemctl restart conceptforge

# 启动 / 停止服务
sudo systemctl start conceptforge
sudo systemctl stop conceptforge

# 测试并重载 Nginx（修改 nginx 配置后）
sudo nginx -t && sudo systemctl reload nginx

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

## 排错提示

### 1. 端口 8000 被占用

后端服务监听 `127.0.0.1:8000`。如启动失败提示端口占用：

```bash
sudo ss -tlnp | grep 8000   # 查看占用进程
sudo systemctl restart conceptforge
```

### 2. Let's Encrypt 证书申请失败

- 确认域名 A 记录已解析到当前服务器公网 IP（`dig <域名>` 与 `curl ifconfig.me` 结果对比）
- 确认 80 端口对公网开放（UFW 已放行）
- 查看证书状态：`sudo certbot certificates`
- 查看详细日志：`sudo less /var/log/letsencrypt/letsencrypt.log`
- 命中速率限制时，需等待一段时间后重试

### 3. conceptforge 服务起不来

```bash
sudo systemctl status conceptforge        # 查看失败原因
sudo journalctl -u conceptforge -n 200    # 查看详细日志
```

常见原因：

- `.env` 文件格式错误（检查是否有非法字符、变量名拼写）
- 虚拟环境损坏，重新创建：

  ```bash
  sudo rm -rf /opt/conceptforge/backend/.venv
  sudo python3 -m venv /opt/conceptforge/backend/.venv
  sudo /opt/conceptforge/backend/.venv/bin/pip install -r /opt/conceptforge/backend/requirements.txt
  sudo systemctl restart conceptforge
  ```

- 代码拉取不完整：重新运行部署脚本即可（脚本幂等）

### 4. Nginx 502 Bad Gateway

后端未就绪或端口不对：

```bash
sudo systemctl status conceptforge
curl -s http://127.0.0.1:8000/api/health   # 直接测试后端
```

## 文件位置说明

| 路径 | 说明 |
| --- | --- |
| `/opt/conceptforge/` | 代码仓库克隆位置 |
| `/opt/conceptforge/backend/.venv/` | Python 虚拟环境 |
| `/opt/conceptforge/backend/.env` | 环境变量配置（需手动填入 LLM key） |
| `/opt/conceptforge/backend/requirements.txt` | Python 依赖清单 |
| `/etc/systemd/system/conceptforge.service` | systemd 服务单元 |
| `/etc/nginx/sites-available/conceptforge` | Nginx 站点配置 |
| `/etc/nginx/sites-enabled/conceptforge` | Nginx 启用的站点（软链） |
| `/var/log/nginx/error.log` | Nginx 错误日志 |
| `/var/log/letsencrypt/` | Let's Encrypt 证书日志（仅申请证书后存在） |
