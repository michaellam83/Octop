# v1.0.1 提交与版本发布步骤

## 1. 当前状态判断

当前版本可以作为 v1.0.1 候选版本，但正式提交前要先处理工作区审查：一期改造包含后端、前端、桌面端、数据库迁移、资源文件和测试文件，不能直接用“全部文件提交”代替审查。

正式版本建议满足以下条件：

- 代码、测试、迁移和发布资源都在预期范围内。
- 没有 API Key、密码、`.env`、本地数据库、备份和日志进入 Git。
- 全新数据目录可以初始化；已有验证数据不作为部署前提。
- 普通专家和通联发仔的链路边界都已回归验证。
- 测试服务器部署和核心用例通过后再创建正式 tag。

## 2. 本地检查

在仓库根目录执行：

```bash
git status --short
git diff --check
git diff --stat
uv sync
make check-all
make build
git status --short
git diff --check
```

如果本机 uv 缓存目录没有写权限，可以改用临时缓存目录：

```bash
UV_CACHE_DIR=/tmp/octop-uv-cache make check-all
```

一期建议额外执行重点测试：

```bash
uv run pytest tests/integration/test_setup_bootstrap.py -q
uv run pytest tests/integration/test_agent_skill_packages.py -q
uv run pytest tests/unit/agents/test_managed_runtime.py tests/unit/agents/test_zdx_direct.py -q
cd dashboard && npx tsc -b
```

如果项目当前 Makefile 使用的是 `make all` 而不是 `make check-all`，以仓库实际目标为准；两者都应覆盖格式、静态检查、类型检查和测试。

## 3. 提交前文件审查

重点检查以下内容不能提交：

- `.env`、配置文件中的真实密码和 API Key。
- `~/.octop` 或项目内导出的 SQLite/PostgreSQL 数据库。
- 用户工作区、上传附件、聊天备份、日志和本地缓存。
- 个人桌面打包产物、临时截图和测试导出文件。
- 与一期改造无关的临时修改。

建议按功能分组暂存，而不是盲目执行 `git add -A`：

```bash
git status --short
git add dashboard/ src/ tests/ desktop/ docs/company-ai-workbench/v1.0.1
git diff --cached --stat
git diff --cached --check
```

如果工作区里还有与一期无关的修改，应先拆分暂存范围，或者把无关修改留在工作区，不要混进 v1.0.1 提交。

## 4. 创建分支和提交

如果当前还没有专用发布分支：

```bash
git switch -c codex/v1.0.1-allinpay
git status --short
```

确认暂存区内容后提交：

```bash
git commit -m "feat: deliver AllinpayAI v1.0.1 company workbench"
git log -1 --oneline
git status --short
```

推荐的团队流转方式是：

```text
codex/v1.0.1-allinpay -> develop -> release/1.0.1 -> main
```

当前本地分支和远端分支实际情况应以团队仓库为准；不要绕过评审直接把工作分支推到生产分支。

推送工作分支：

```bash
git push -u origin codex/v1.0.1-allinpay
```

## 5. 测试通过后创建正式 tag

合并到发布目标分支并在测试环境回归通过后，再执行：

```bash
git switch main
git pull --ff-only origin main
git log -1 --oneline
git tag -a v1.0.1 -m "AllinpayAI v1.0.1"
git push origin v1.0.1
```

创建 tag 前必须确认远端没有同名正式 tag。如果远端仓库无法访问或 DNS 不通，应先恢复网络后再确认，不能凭本地 tag 列表推断远端状态。

## 6. 发布交付物

建议保留以下交付信息：

- Git commit SHA 和 `v1.0.1` tag。
- 测试服务器部署时间、镜像 tag 和数据目录位置。
- 使用过的数据库迁移版本。
- 管理员初始化方式、测试账号和验证用例结果。
- 失败日志、已知限制和下一期计划。

Web/服务器发布以源码 commit 或容器镜像为准；macOS App 发布以该版本源码生成的桌面构建产物为准，不能把未对应 commit 的本地 App 当作正式版本。
