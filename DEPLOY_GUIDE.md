# Water API 快速部署指南

## 概述

`deploy.sh` 是一个自动化部署脚本，可以快速将您本地修改的代码部署到服务器。

## 前置要求

### 1. 安装 sshpass（用于非交互式 SSH 登录）

**Ubuntu/Debian:**
```bash
sudo apt-get install sshpass
```

**macOS:**
```bash
brew install sshpass
```

**Windows (WSL):**
```bash
sudo apt-get install sshpass
```

### 2. 确保脚本有执行权限

```bash
chmod +x deploy.sh
```

## 使用方法

### 基本用法

```bash
bash deploy.sh [命令]
```

### 可用命令

| 命令 | 说明 |
|-----|-----|
| `faka` | 仅部署发卡程序 |
| `oneapi` | 仅部署 One-API |
| `all` | 部署所有（默认） |
| `status` | 检查部署状态 |
| `help` | 显示帮助信息 |

## 常见使用场景

### 场景 1：修改了发卡程序（faka_app.py）

```bash
# 1. 修改代码
vim faka_app.py

# 2. 运行部署脚本
bash deploy.sh faka

# 3. 查看结果
# 脚本会自动上传文件并重启容器
```

### 场景 2：修改了 Docker 配置（docker-compose.yml）

```bash
# 1. 修改配置
vim docker-compose.yml

# 2. 运行部署脚本
bash deploy.sh oneapi

# 3. 等待容器重启完成
```

### 场景 3：同时修改了多个文件

```bash
# 运行完整部署
bash deploy.sh all

# 或直接运行（不指定参数默认为 all）
bash deploy.sh
```

### 场景 4：检查部署状态

```bash
bash deploy.sh status
```

## 脚本工作流程

```
修改代码
   ↓
运行 bash deploy.sh
   ↓
脚本检查 sshpass
   ↓
上传文件到服务器
   ↓
执行远程命令重启容器
   ↓
部署完成
```

## 脚本配置

脚本中包含的服务器信息：

```bash
SERVER_IP="144.202.121.4"           # 服务器 IP
SERVER_USER="root"                   # SSH 用户
SERVER_PASSWORD="5_XuT*ZGC_3m(F?J"  # SSH 密码
PROJECT_PATH="/opt/one-api"          # 项目路径
```

**如果服务器信息变更，需要修改脚本中的这些变量。**

## 部署流程详解

### 发卡程序部署 (faka)

1. 检查 `faka_app.py` 文件是否存在
2. 通过 SCP 上传文件到服务器的 `/opt/one-api/faka_app.py`
3. 执行 `docker restart faka` 重启容器
4. 容器会自动加载新的代码
5. 发卡页面立即生效

### One-API 部署 (oneapi)

1. 检查 `docker-compose.yml` 文件是否存在
2. 通过 SCP 上传文件到服务器
3. 执行 `docker-compose up -d` 重启服务
4. Docker 会自动处理容器的启动和更新

## 常见问题

### Q: 脚本提示 "sshpass 未安装"

**A:** 运行以下命令安装：
```bash
sudo apt-get install sshpass
```

### Q: 部署失败，提示 "Permission denied"

**A:** 可能是以下原因：
1. 服务器密码错误 - 检查 `SERVER_PASSWORD` 变量
2. SSH 密钥权限问题 - 尝试重新生成 SSH 密钥
3. 文件权限问题 - 确保本地文件可读

### Q: 部署后容器没有重启

**A:** 检查以下几点：
1. 服务器连接是否正常：`bash deploy.sh status`
2. Docker 是否正常运行：`docker ps`
3. 查看容器日志：`docker logs faka` 或 `docker logs one-api`

### Q: 如何查看部署日志？

**A:** 登录服务器查看容器日志：
```bash
ssh root@144.202.121.4

# 查看发卡程序日志
docker logs faka

# 查看 One-API 日志
docker logs one-api

# 实时查看日志
docker logs -f faka
```

### Q: 如何回滚到上一个版本？

**A:** 
1. 从 GitHub 检出上一个版本：
   ```bash
   git log --oneline  # 查看提交历史
   git checkout <commit-hash>  # 切换到特定版本
   ```
2. 运行部署脚本：
   ```bash
   bash deploy.sh
   ```

## 高级用法

### 自定义服务器配置

如果您有多个服务器，可以创建多个脚本版本：

```bash
cp deploy.sh deploy-prod.sh
# 编辑 deploy-prod.sh，修改 SERVER_IP 等信息
bash deploy-prod.sh
```

### 集成到 CI/CD

您可以将部署脚本集成到 GitHub Actions：

```yaml
name: Deploy Water API

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: bash deploy.sh
        env:
          SERVER_PASSWORD: ${{ secrets.SERVER_PASSWORD }}
```

## 安全建议

1. **不要在公开仓库中提交密码**：使用环境变量或 `.env` 文件
2. **定期更换密码**：建议每月更换一次 SSH 密码
3. **使用 SSH 密钥认证**：比密码认证更安全
4. **限制脚本权限**：只在需要时运行部署脚本

## 支持

如有问题，请：
1. 检查脚本输出的错误信息
2. 查看服务器日志：`docker logs`
3. 提交 Issue 到 GitHub

---

**快速部署示例**

```bash
# 克隆仓库
git clone https://github.com/LimeChin/OpenWater.git
cd OpenWater

# 修改代码
vim faka_app.py

# 部署
bash deploy.sh faka

# 完成！
```

就这么简单！🚀
