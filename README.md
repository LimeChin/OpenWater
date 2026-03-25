# Water API - Token 副业项目

一个基于 One-API 的 Token 销售平台，支持多种 AI 模型的聚合与转售。

## 项目概述

Water API 是一个完整的 Token 销售解决方案，集成了：
- **One-API**：AI 模型聚合平台
- **发卡系统**：自动化充值与兑换
- **支付集成**：虎皮椒微信支付
- **多渠道支持**：OpenRouter、Groq、DeepSeek 等

## 核心特性

### 1. 积分制定价
- **1 元 = 10,000 积分**
- 用户充值 1 元即获得 10,000 积分
- 清晰的计费逻辑，易于用户理解

### 2. 完整的支付闭环
```
用户支付 1 元 → 发卡系统生成兑换码 → 用户在 One-API 兑换 → 额度到账
```

### 3. 多渠道 API 支持
- **OpenRouter**：极低价付费模型（Google Gemma 等）
- **Groq**：超高速推理，慷慨免费额度
- **DeepSeek**：国内最强模型，价格极低

### 4. 虎皮椒微信支付
- 个人即可开通
- 费率低廉
- 资金直接到账

## 快速开始

### 前置要求
- Docker & Docker Compose
- Vultr 或其他云服务器（推荐 1GB+ 内存）
- 虎皮椒支付账户

### 部署步骤

1. **克隆仓库**
```bash
git clone https://github.com/LimeChin/OpenWater.git
cd OpenWater
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env，填入您的 API 密钥和支付信息
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问应用**
- One-API 后台：http://your-server-ip:3000
- 发卡页面：http://your-server-ip:3001

## 项目结构

```
OpenWater/
├── docker-compose.yml      # Docker 编排配置
├── Dockerfile              # 发卡程序 Docker 镜像
├── faka_app.py            # 发卡程序核心代码
├── .env.example           # 环境变量示例
├── .gitignore             # Git 忽略文件
└── README.md              # 项目说明
```

## 关键配置

### One-API 配置
- **管理员账号**：admin2026
- **超级管理令牌**：SystemAdminToken（无限额度）
- **单位美元额度**：1（确保显示为原始数值）

### 发卡程序配置
- **端口**：3001
- **积分换算**：QUOTA_PER_YUAN = 10000
- **数据库**：直接操作 One-API 的 SQLite 数据库

### 支付配置
- **支付网关**：https://api.xunhupay.com/payment/do.html
- **费率**：约 2-3%
- **结算**：T+1

## API 渠道接入

### OpenRouter
```
类型：OpenAI 兼容
地址：https://openrouter.ai/api/v1
模型：google/gemma-2-9b-it（极低价）
```

### Groq（可选）
```
类型：OpenAI 兼容
地址：https://api.groq.com/openai/v1
模型：mixtral-8x7b-32768（免费）
```

### DeepSeek（可选）
```
类型：OpenAI 兼容
地址：https://api.deepseek.com/v1
模型：deepseek-chat
```

## 使用流程

### 用户侧
1. 访问发卡页面（http://your-server-ip:3001）
2. 输入充值金额（如 1 元）
3. 扫码支付（微信）
4. 获得兑换码
5. 在 One-API 充值页面粘贴兑换码
6. 额度到账，开始使用

### 运营侧
1. 登录 One-API 后台（admin2026 账号）
2. 在"渠道"菜单管理 API 渠道
3. 在"令牌"菜单创建用户令牌
4. 在"运营设置"调整定价和显示
5. 在"总览"查看收入统计

## 常见问题

### Q: 如何修改积分比例？
A: 修改 `faka_app.py` 中的 `QUOTA_PER_YUAN` 参数，然后重启容器。

### Q: 如何添加新的 API 渠道？
A: 在 One-API 后台的"渠道"菜单中点击"添加新的渠道"，填入相应的 API 密钥和配置。

### Q: 支付失败怎么办？
A: 检查虎皮椒账户余额和 AppID/密钥配置是否正确。

### Q: 如何查看收入？
A: 在虎皮椒后台查看订单记录，或在 One-API 的"总览"查看用户充值统计。

## 安全建议

1. **修改默认密码**：立即修改 admin2026 的密码
2. **关闭注册**：在"系统设置"中关闭"允许新用户注册"
3. **定期备份**：备份 One-API 的数据库文件
4. **隐藏敏感信息**：不要在代码中提交 API 密钥

## 技术栈

- **后端**：One-API (Go)、Flask (Python)
- **数据库**：SQLite
- **容器化**：Docker & Docker Compose
- **支付**：虎皮椒 (Xunhupay)
- **API 聚合**：OpenRouter、Groq、DeepSeek

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

**项目启动日期**：2026-03-20  
**最后更新**：2026-03-25  
**当前版本**：v1.0.0-beta
