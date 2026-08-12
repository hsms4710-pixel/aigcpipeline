# P6 Spec：DCC 资产加工层（Agent 控制 DCC，横切能力）

> 状态：**规划中** ｜ 复用：dcc-mcp-creator（intern-learn 664011，dcc-mcp-core 0.18.39 生态）
> 定位：不是独立 Part，而是 P1(3D 扩展)/P2/P4 共用的**资产加工横切层**——让 Agent 通过 MCP 控制 DCC 完成建模/UV/绑定/表情/导出，替代人工 DCC 操作。

## 1. 为什么需要
- AIGC 生成的 3D 资产（Hunyuan3D/TRELLIS）直接进引擎**不可用**：需要清理网格、减面、UV、PBR 材质、绑定、表情 morph、格式导出
- 2D 立绘分层后需要绑定（Live2D/Spine）——也是 DCC 环节
- 工业流程：生成 → **DCC 加工** → 引擎/Mod；Agent 若不能操作 DCC，管线就断在"人"这里

## 2. 复用基础（已有资产）
- **dcc-mcp-creator**：自研 DCC-MCP 适配器构建 skill（Nuke/Blender/3ds Max/UE/ZBrush/Houdini/Maya）
  - 架构原语：`DccServerBase`（MCP/HTTP + skill 目录）、`HostExecutionBridge`（DCC API 调度）、gateway daemon（路由/能力发现）、sidecar（Rust，host RPC ↔ MCP/REST）
  - 关键约束：不在 Tokio/HTTP 线程碰 DCC API；headless 模式优先；typed skill 优于裸脚本
  - 位置：`intern-learn/intern-learn/game-dev/664011-自研DCC-MCP.../dcc-mcp-creator/`（含 references + 打包 zip）
- **layout-forge dccBridge**（664168 关卡AI工具链）：关卡数据导出到 DCC/引擎的经验（UE 等）→ 引擎侧 Bridge 参照

## 3. 架构（接入管线）
```
AIGC 资产（glTF/PNG 分层）
   → [P6 DCC 加工层]
        DccServerBase(Blender) + HostExecutionBridge + gateway
        skill: asset_cleanup / retopo / uv_pack / pbr_setup / add_blendshape / export_gltf
   → 引擎就绪资产（P1 3D 扩展 / P4 引擎接入 / P2 过场）
```
- 宿主：**Blender 优先**（Python 内嵌、headless 可跑、隔离环境友好、导出 glTF 成熟）
- 协议：与 P3 一致走 MCP/HTTP，Agent 通过 gateway 调用 DCC skill
- 运行：DCC 与 ComfyUI/TTS 同在隔离环境容器；Blender headless 无 UI

## 4. 场景与顺序
| 场景 | 内容 | 进入时机 |
|---|---|---|
| S1 3D 资产加工 | 3D 模型 → 清理/减面/UV/PBR/加 blendshape → 导出 glTF | P1 3D 扩展（后置） |
| S2 2D 分层绑定 | 分层 PSD → Live2D/Umamo 绑定（人工/半自动 + DCC 辅助） | P1 可选 |
| S3 引擎导出 | Blender-MCP 导出 Godot/Unity/UE 资源 | P4 |
| S4 过场 | Blender/UE 镜头/动画 | P2 |
| S5 Mod 注入辅助 | 现有游戏资产注入/回归检查 | P4 POC |

## 5. MVP 范围
- Blender headless + 1 个 adapter（asset_cleanup + add_blendshape + export_gltf 三个 skill）
- 验证：一个 Hunyuan3D/TRELLIS 生成物 → Blender-MCP 加工 → Godot 可导入
- 复用 dcc-mcp-creator skill 直接搭，不重写框架

## 6. 验收（gate，随 P1-3D/P4 走）
- [ ] Blender headless 在隔离环境跑通，Agent 通过 MCP 调用 3 个 skill
- [ ] 加工后资产通过 validate-asset-package + Godot 可导入
- [ ] 表情 blendshape 集（ARKit 子集）加入模型并可在 Godot 驱动
