# 测试服务器部署步骤

## 1. 推荐部署方式

测试环境推荐使用 Docker Compose，使用独立数据目录和独立域名/端口，不复用开发机的 `~/.octop`、数据库、用户凭据和附件目录。

```text
测试服务器
  -> AllinpayAI v1.0.1 容器
  -> 独立数据目录
  -> 可选反向代理和 HTTPS
  -> 智多星接口、Tavily 和其他外部服务
```

## 2. 测试服务器环境要求

### 最低建议

- Linux x86_64 或 arm64，建议 Ubuntu 22.04/24.04 或同等级 Debian 系统。
- 2 vCPU、4 GB 内存、20 GB 可用磁盘。
- Docker Engine 24+、Docker Compose v2、BuildKit。
- 服务器能够通过 HTTPS 访问代码仓库、依赖镜像、智多星接口和 Tavily；如果网络受限，需要准备内部镜像仓库和出口白名单。
- 放通测试访问端口（默认 `8088`），生产式使用时建议只开放反向代理的 443 端口。
- 正确的 NTP/系统时间；相对日期查询依赖服务端时间。

### 推荐配置

- 4 vCPU、8 GB 内存、40 GB 以上 SSD。
- 数据目录单独挂载，便于备份和更换容器。
- 使用 HTTPS、反向代理和访问控制，不把带有管理员入口的 8088 直接暴露到公网。
- 单实例测试可以使用 SQLite；多人并行或长期测试建议使用 PostgreSQL。

### Docker 部署不需要安装的工具

仅使用容器部署时，测试服务器不需要安装 Node、Go、Wails、Playwright 或本地前端构建工具；这些工具在构建阶段或镜像中处理。

### 非容器部署补充要求

如果不使用 Docker，则至少需要 Python 3.12+、uv、Node 24 和项目要求的系统依赖；生产测试环境不建议直接使用本地开发命令替代容器启动。

## 3. 准备目录和源码

以下示例使用 `/srv/allinpay-ai` 作为测试部署目录：

```bash
sudo mkdir -p /srv/allinpay-ai
sudo chown -R "$USER":"$USER" /srv/allinpay-ai
cd /srv/allinpay-ai
git clone <company-repository-url> source
cd source
git checkout <v1.0.1-commit-or-tag>
mkdir -p /srv/allinpay-ai/data
```

如果公司仓库不允许测试服务器直接 clone，可以在构建机生成镜像后推送到内部镜像仓库，再在测试服务器只执行镜像拉取和启动。

## 4. 配置环境变量

在部署目录创建只允许部署账号读取的环境文件，例如 `docker/.env`：

```dotenv
OCTOP_PORT=8088
OCTOP_DATA=/srv/allinpay-ai/data
OCTOP_ADMIN_USERNAME=admin
OCTOP_DEFAULT_PASSWORD=请替换为测试环境管理员密码
OCTOP_LOG_LEVEL=info
```

实际变量名以当前仓库的 `docker/docker-compose.yml`、`config.py` 和部署脚本为准。不要把这个文件提交到 Git，也不要在截图或聊天记录中展示真实密码、智多星 key、Tavily key。

## 5. 构建并启动

从源码构建测试镜像：

```bash
bash docker/docker_build.sh allinpay-ai:v1.0.1
```

启动 Compose：

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build
docker compose --env-file docker/.env -f docker/docker-compose.yml ps
docker compose --env-file docker/.env -f docker/docker-compose.yml logs -f --tail=200 octop
```

当前 Compose 文件如果仍把服务镜像写死为 `octop:latest`，有两种处理方式：

1. 使用当前 checkout 直接 `up -d --build`，确保构建上下文就是 v1.0.1 commit。
2. 复制一份测试环境 Compose override，把服务镜像明确改为 `allinpay-ai:v1.0.1`，避免测试机继续使用旧的 `latest`。

不要用 `latest` 作为长期验收依据；验收记录应记下 commit SHA 或不可变镜像 tag。

## 6. 首次初始化和验证

容器启动后按以下顺序验证：

1. 打开 `http://测试服务器:8088` 或反向代理地址，确认进入初始化/登录页面。
2. 使用测试管理员账号登录；如果部署脚本生成了初始密码文件，只从服务器受控目录读取，不通过聊天或截图传播。
3. 新建一个普通测试用户，配置该用户自己的智多星 userid/key。
4. 在管理员侧配置 Tavily 公共搜索凭据，执行一次公网搜索验证。
5. 使用普通用户验证通联发仔的内部业务查询、相对日期查询、公网搜索和 Token 统计。
6. 使用普通用户验证普通专家的 Provider、技能、连接器、知识库、附件和通道能力。
7. 验证普通用户看不到自动化、帮助与反馈、项目地址等一期隐藏入口；通联发仔不显示快捷指令和专家选择。
8. 重启容器，再次验证用户、模板、智多星 key 和历史会话仍然存在。

## 7. 健康检查和日志

```bash
curl -fsS http://127.0.0.1:8088/api/health
docker inspect --format='{{json .State.Health}}' octop
docker compose --env-file docker/.env -f docker/docker-compose.yml logs --tail=200 octop
```

如果使用反向代理，再从外部访问一次登录页、静态资源和 SSE 对话流，确认代理没有缓存或截断流式响应。

## 8. 测试环境安全要求

- 8088 不直接暴露到公网；至少使用防火墙、VPN 或反向代理访问。
- 使用专用测试智多星和 Tavily 凭据，不使用生产 key。
- 每次验收使用独立数据目录；不要把上一套项目的数据库复制到本项目。
- `.env`、数据库、备份、日志和用户上传附件只保留在服务器受控目录。
- 测试账号、密码和外部服务 key 由管理员单独分发，不能写进版本文档和 Git。
