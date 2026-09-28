# 测试环境迭代与更新步骤

## 1. 先区分两类更新

### A. 托管模板内容更新

管理员只修改通联发仔的提示词、欢迎语、快捷问题、任务示例或技能包清单时，通常可以通过管理界面保存并发布，不需要重新构建容器镜像。更新后要验证模板版本、用户侧重载和新会话行为。

### B. 代码和运行时更新

涉及后端、前端、数据库迁移、直链协议、搜索预处理、权限、通道或桌面资源时，需要生成新的 commit/镜像，备份测试数据后再更新服务。

## 2. 推荐迭代流程

```text
开发修改
  -> 本地检查和测试
  -> 提交工作分支并评审
  -> 构建带 commit 的测试镜像
  -> 备份测试数据
  -> 更新测试服务器
  -> 健康检查和一期回归
  -> 记录问题和验收结果
  -> 合并/打 tag
```

## 3. 本地变更检查

每次准备更新前执行：

```bash
git status --short
git diff --check
make check-all
make build
```

前端变更追加：

```bash
cd dashboard
npx tsc -b
```

如果变更涉及一期托管专家，至少回归：

- 用户级智多星 userid/key 隔离。
- 通联发仔内部业务查询和相对日期处理。
- Tavily 公网搜索、超时和额度错误。
- 普通专家 Provider、技能、连接器、知识库、附件和通道。
- 管理员模板发布、用户侧重载和权限边界。
- Token 统计、错误展示和服务重启后的数据持久化。

## 4. 构建带 SHA 的测试镜像

在仓库根目录执行：

```bash
git rev-parse --short HEAD
docker build -f docker/Dockerfile \
  -t allinpay-ai:v1.0.1-<short-sha> \
  -t allinpay-ai:test-latest .
```

长期验收使用 `v1.0.1-<short-sha>` 这样的不可变 tag；`test-latest` 只作为方便测试的临时别名。

如果使用内部镜像仓库：

```bash
docker tag allinpay-ai:v1.0.1-<short-sha> <registry>/allinpay-ai:v1.0.1-<short-sha>
docker push <registry>/allinpay-ai:v1.0.1-<short-sha>
```

## 5. 更新前备份

在测试服务器上先备份数据库、用户工作区、会话和相关配置。若容器名为 `octop`，可以使用项目 CLI 备份：

```bash
docker exec octop octop backup create \
  -o /data/.octop/backups/pre-update-$(date +%Y%m%d-%H%M%S).tar.gz \
  --include-chats
```

同时在宿主机记录当前镜像、commit、容器状态和数据目录：

```bash
docker inspect octop > /srv/allinpay-ai/backup/pre-update-container.json
docker image inspect allinpay-ai:test-latest > /srv/allinpay-ai/backup/pre-update-image.json
docker compose --env-file docker/.env -f docker/docker-compose.yml ps > /srv/allinpay-ai/backup/pre-update-compose.txt
```

备份成功后再执行数据库迁移或替换镜像。不要通过删除表或删除整个数据目录解决升级问题。

## 6. 更新服务

源码部署方式：

```bash
cd /srv/allinpay-ai/source
git fetch origin
git checkout <new-commit-or-tag>
docker compose --env-file docker/.env -f docker/docker-compose.yml build
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d
docker compose --env-file docker/.env -f docker/docker-compose.yml ps
docker compose --env-file docker/.env -f docker/docker-compose.yml logs --tail=200 octop
```

镜像部署方式：

```bash
docker pull <registry>/allinpay-ai:v1.0.1-<short-sha>
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d
```

Compose 文件应明确引用本次镜像 tag；如果仍使用 `octop:latest`，先更新测试环境 override 或 compose 配置，避免启动旧镜像。

数据库迁移会在服务启动时按项目设计执行。启动日志中应确认迁移成功，不能把迁移失败当作服务正常启动。

## 7. 更新后检查

```bash
curl -fsS http://127.0.0.1:8088/api/health
docker compose --env-file docker/.env -f docker/docker-compose.yml ps
docker compose --env-file docker/.env -f docker/docker-compose.yml logs --tail=200 octop
```

浏览器验收顺序建议如下：

1. 管理员登录，确认版本、用户、普通模型和托管模板页面可打开。
2. 普通用户登录，确认通联发仔可启动，且不显示不适用的快捷指令和专家选择。
3. 提问一个内部业务查询，确认使用当前用户的智多星 key。
4. 提问一个相对日期业务问题，确认时间被正确解析后再查询。
5. 明确要求联网搜索，确认搜索事件、结果整理和来源展示符合预期。
6. 切换普通专家，确认普通 Provider、Skill、Connector、知识库和附件能力没有被托管链路破坏。
7. 从 QQ 等已配置通道发送一次消息，确认与 Web 使用同一套用户隔离和错误处理。
8. 查看 Token 统计，确认普通专家和通联发仔的用量均有记录。
9. 重启容器后重复第 2 至第 8 项的关键用例。

## 8. 回滚原则

- 首选回滚到上一个已验证的镜像 tag，不要先删除数据库。
- 只要新版本已经执行了不可逆数据库迁移，就不能简单把旧镜像挂回去；先检查迁移兼容性和备份。
- 回滚前保留失败版本日志和当前数据快照。
- 只有在明确确认备份完整、服务已停止且数据兼容时，才执行完整数据恢复。
- 回滚后重新执行健康检查、登录、通联发仔、普通专家和通道用例。

## 9. 后续迭代建议

- 增加企业 SSO 和用户级智多星凭据自动发放/回收。
- 为公网搜索增加可观测性，包括搜索耗时、来源、重试、超时和额度状态。
- 在权限可控的前提下评估通联发仔附件解析，而不是直接复用普通专家的全部工具。
- 增加托管模板预览、灰度发布和一键回滚。
- 多实例和长期测试场景切换到 PostgreSQL，并完善备份恢复演练。
