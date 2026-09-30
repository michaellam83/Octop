# 公司 AI 工作台改造文档

本目录记录基于 Octop 的公司内部 AI 工作台改造方案。

目标项目：`/Users/michaellin/MLproject/TLOctop2/octop20260920`

当前阶段：第一阶段改造完成，待管理员重新初始化验证

第一阶段目标：完成“通联智多星 + 通联发仔”后端闭环，使管理员可以配置用户级智多星凭据，系统可以为新用户自动创建不可删除、不可编辑的“通联发仔”专家，并支持启动、停用和配置刷新，完成后进入内部验证。

## 文档

- [第一阶段实施方案](./phase-1-plan.md)
- [第一阶段验证清单](./phase-1-validation.md)

## 当前明确的设计决定

- 智多星不是 Octop Provider，也不通过 Skill 调用；“通联发仔”使用独立的用户级直连模型适配器。
- 普通 Provider、普通 Agent 和 Octop 原生 Skill/MCP 链路保持原有行为。
- 智多星 Key 由管理员按用户配置，用户不在首次使用时自行填写。
- 每个用户的 `ZDX_API_KEY` 加密保存，`ZDX_USERID` 直接使用管理员录入的真实 OA username。
- 本地验证阶段由管理员录入用户真实 OA username，不引入 OA / 企业微信扫码登录。
- 智多星调用后端业务或系统时必须传递 `chatBizOptions.userid`，用于权限和可读范围校验。
- 智多星 API Key 与 `userid` 是绑定关系，服务端会校验二者是否匹配。
- “通联发仔”模板 ID 固定为 `tonglian-fazai`。
- 用户实例名称统一为“通联发仔”，Agent ID 沿用 Octop 自动生成的短 ID。
- 用户实例标记为系统托管，只显示对话和启用/停用操作。
- 第一阶段不做公司 Logo、Icon、整体视觉改造，不接入 OA 之外的业务系统 MCP。
