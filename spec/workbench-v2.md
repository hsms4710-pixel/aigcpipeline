# 工作台 v2 规划（spec/workbench-v2.md）—— AIGC 流水线统一入口

> 状态：**重要开发阶段（用户 2026-08-13 确认）** ｜ 目标：本页面是后续所有 AIGC 流水线（形象/语音/过场/Agent/评测）的入口，需可扩展、可规划、可运营。

## 1. 定位
工作台 = **流水线指挥台 + 创作空间**：
- 左侧：功能面板（Persona / 资产创建 / 参考图 / 配置）
- 主区：无限画布（创作、编排、预览）
- 未来接入：P2 过场、P3 Agent、V1 语音、P5 评测（按 Part 扩展面板）

## 2. UI 设计（黑灰色暗色主题）
- 背景 #1e1e1e / 面板 #2b2b2b / 卡片 #333 / 边框 #444 / 文字 #e0e0e0 / 强调 #6ea8fe（蓝灰）
- 布局：左侧固定导航（宽度 300，可折叠） + 主区画布 + 顶部状态栏（Job 状态/成本/后端状态）
- 所有面板暗色统一，组件风格一致（按钮/输入/下拉/标签）

## 3. 左侧功能面板（v2 范围）
### 3.1 Persona（角色设定）
- **导入**：上传 persona.json（校验 schema）
- **在线实时创建**：表单编辑器（已有 PersonaForm，改暗色）→ 生成 persona.json
- **LLM 填充**：输入一句话人设 → 调 LLM（配置的 key）生成完整 persona（visual/style/assets）→ 可再编辑
### 3.2 资产创建（图像）
- 选择**意图/资产类型**（按 prompt-templates）：
  - 立绘（展示用）/ 三视图 / 对话用无边框立绘（表情差分）/ 像素小人三视图 / 像素三视图 / 行为帧 / 精灵表
- 选择参考图（风格参考：方舟/FGO/坎公/pixiv）
- 选择生图后端（openai/gemini/fal）+ 角色（persona）
- 生成 → Job 队列 → 画布呈现 + 资产树
### 3.3 参考图库
- 管理参考图（导入/列表/预览/标记：立绘风格/差分/像素小人）
- 内置：arknights_amiya / prts_diff / fgo_artoria（后续扩充坎公等）
### 3.4 配置（设置）
- **API Keys**：GPT（中转站 base_url+key）/ Gemini / FAL / TTS（火山/Azure）/ LLM（DeepSeek 等）——存入 env/.env（不入库），界面可改
- 生图后端选择（openai/gemini/fal）+ 默认模型
- 参考图/输出目录
### 3.5 角色/资产库
- 角色列表（persona + 资产树）→ 点开预览、添加到画布、重新生成

## 4. 主区无限画布（v2 增强）
- 保留 tldraw 画布；角色板/资产节点/分镜板模板
- 生成产物自动入画布（已有）
- v2 追加：Job 状态悬浮层、资产拖拽整理

## 5. 后端 API（v2 新增）
- `POST /api/persona/llm`：一句话 → LLM 生成 persona（需 LLM key）
- `POST /api/config`：保存/读取 API key（env/.env，掩码显示）
- `GET /api/refs`：参考图列表
- `GET /api/templates`：资产意图模板列表
- 复用：characters/generate/jobs

## 6. 实施阶段（v2 拆解）
| 阶段 | 内容 |
|---|---|
| v2.0 | 暗色主题 + 左侧面板框架（Persona 导入/创建、资产创建、参考图、配置） |
| v2.1 | LLM 填充人设 + 配置 API key 界面 |
| v2.2 | 参考图库管理 + 意图模板选择完整化 |
| v2.3 | 接入 V1 语音 / P2 过场入口（流水线扩展） |

## 7. 边界
- v2 聚焦"形象资产创建入口"（P1 全流程），语音/过场/Agent 作为后续面板扩展（不一次做完）
- 不引入重型状态管理（先 React hooks + 轻量）
- API key 只在本地 env/.env，前端掩码显示不回显
