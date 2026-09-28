# AllinpayAI v1.0.1

## 版本定位

本目录记录从开源 Octop 基线到 AllinpayAI 一期封版候选状态的改造结果、使用范围和部署流程。

当前仓库的 `pyproject.toml` 版本已经是 `1.0.1`，本地 `main` 分支基于上游 Octop 1.0.1 相关提交。当前工作区仍包含一期改造的未提交文件，因此这里描述的是“v1.0.1 候选工作区”，不是已经打过 Git tag 的正式发布版本。

## 文档索引

- [01-change-summary.md](./01-change-summary.md)：从开源版本到当前状态的重点改造内容和边界。
- [02-user-scope-and-zdx-comparison.md](./02-user-scope-and-zdx-comparison.md)：普通用户功能范围，以及与智多星平台原生 Web 的定位对比。
- [03-release-and-submit.md](./03-release-and-submit.md)：当前版本检查、提交、分支和打 tag 流程。
- [04-test-server-deployment.md](./04-test-server-deployment.md)：测试服务器环境要求和首次部署步骤。
- [05-iteration-and-update.md](./05-iteration-and-update.md)：测试环境部署后的迭代、更新、回滚和回归步骤。

## 当前架构边界

```text
普通专家
  -> Octop Provider / Harness Agent / Skill / Connector / Knowledge Base

通联发仔
  -> 每个用户自己的智多星 userid + key
  -> 智多星直链调用
  -> 由托管模板统一控制提示词、联网预处理和可见能力
```

一期的核心原则是：智多星用户级 key 只服务于“通联发仔”专用链路，不把它注册为普通 Provider，也不让普通专家意外继承该 key；管理员新增的普通模型配置则继续服务于普通专家。

## 封版前置检查

建议在提交 v1.0.1 前完成以下验证：

1. `make check-all`、前端类型检查和生产构建通过。
2. 使用全新数据目录完成一次初始化，确认管理员、普通用户、用户级智多星 key 和 Tavily 配置流程可用。
3. 验证“通联发仔”能够执行智多星内部业务查询、相对日期查询和公网搜索；验证失败时不会把错误框重复追加到同一条对话中。
4. 验证普通专家仍可使用管理员配置的普通 Provider、技能、连接器、知识库、附件和工具能力。
5. 验证托管模板更新后能发布到所有用户的“通联发仔”，并且普通专家不会使用托管专家的专用模型配置。
6. 确认提交内容不包含 `.env`、数据库、备份、日志、API Key、用户工作区和本机打包产物。
