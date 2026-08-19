# 3D 模型路线重新调研（spec/plan-3d-route.md）

> 规划日期：2026-08-18 ｜ 触发：用户「找到之前的 3D 模型路线，重新调研整理一遍」
> 定位：3D 线为**后置可选项**（2D 线优先，见 spec/dev-roadmap-2d3d.md P2-3D 段）；本文档重新调研 2026 年最新方案并给出本机可执行的推荐路线。
> 结论先行：**3D 管线五环（生图→生成→修正→绑骨→动作→引擎）外部替代已全部成熟**；本机 RTX 4060 8GB 可跑 TRELLIS2（低显存模式 512³）与 Hunyuan3D 2.1 形状生成（6GB），全量 16GB 纹理生成需 API 或更高显存；推荐「Tripo API 快速 POC + 本地开源做质量对照」。

---

## 1. 之前的 3D 路线（旧基线）
- spec/pipeline-unified-2d3d.md §2：3D 管线对照网易内部缺口（🔴ailab_auto_skin / CharacterMaker / Motion Completion / PoseCap / Wuzu），替代方案 = Tripo3D/混元3D/Meshy + Blender 修正 + Mixamo/RigNet/Auto-Rig Pro 绑骨
- spec/dev-roadmap-2d3d.md P2-3D：F1 生成（Tripo/混元3D/Meshy）→ F2 Blender 修正 → F3 Mixamo/RigNet 绑骨 → F4 动作 → F5 Godot 导入（3-5 天）
- 旧基线结论：绑骨/蒙皮/动作是缺口集中区，但 Mixamo 可替代

## 2. 2026 最新调研（本文档更新）

### 2.1 生图→3D 生成（image-to-3D）
| 方案 | 性质 | 关键指标（2026） | 本机适用性（RTX 4060 8GB） |
|---|---|---|---|
| **TRELLIS 2**（微软，MIT 开源，4B 参数） | 本地/ComfyUI | 纹理保真 9/10；低显存模式 512³ 约 8GB VRAM，1024³ 低显存 ~120s；256³ 最低 8GB | ✅ 可跑（低显存模式）；12GB 推荐跑 512 标准；16-24GB 跑 1024+ 高质 |
| **Hunyuan3D 2.5 / 2.1**（腾讯，Apache 2.0，~10B 参数） | 本地 | 形状生成最低 6GB VRAM；**形状+纹理全量 16GB**；RTX 3060 12GB 形状 ~30s | ⚠️ 形状生成可跑（6GB）；全量需 API/更高显存。注：2.5 为 research preview（arXiv 2506.16504），本地推理用 2.1 权重 |
| **Tripo v3.1 / H3.1**（VAST，商业 API） | API | PBR 纹理、面数最高 200 万；image-to-3D ~20-40s；Turbo 模式更快 | ✅ API（试用 key 有额度）；**POC 首推** |
| **Meshy v6**（商业 API） | API | 低模优化、硬表面、风格化/低模资产 | ✅ API（备选，偏低模） |
| **Hyper3D Rodin**（商业） | API | 多图/文本→3D（runway 生态） | 备选 |
| 影眸 / hitem3D / seedream | 商业/开源 | 国内生态（网易参考） | 备选 |

**选型判断（2026-08-18）**：
- 质量/成本平衡：**Tripo API 最快见效**（PBR 纹理、Turbo、面数可控），适合做 POC 验证全链路
- 开源对照：**TRELLIS 2 是本机 8GB 显存内质量最优**；Hunyuan3D 2.1 形状生成可在 6GB 跑通（纹理全量需 16GB）
- 不要只依赖一家：管线接口化（provider 抽象），Tripo / TRELLIS2 / Hunyuan3D 可切换

### 2.2 修正链路（DCC）
- Blender（减面/UV/法线传递/贴图）+ DCC-MCP adapter（本仓库已有自研 DCC-MCP 项目经验）
- 生成模型面数多、UV 待改进 → 标准减面→重构 UV→法线传递→贴图流程

### 2.3 自动绑骨 / 蒙皮 / 动作（2026 更新）
| 方案 | 性质 | 说明 |
|---|---|---|
| **Mixamo**（Adobe，免费） | 网页自动绑骨 + 动作库 | 标准模板骨；上传模型自动绑骨蒙皮，动作库量大；**免费基线** |
| **UniRig**（VAST，SIGGRAPH 2025，开源 + Tripo API） | 自动绑骨框架 | 统一模型，支持人类/动物/幻想角色/无机结构；特殊 token 标注骨类型（Mixamo 模板骨/头发布料弹簧骨）；**Tripo API 已提供 /animations/rig 端点（rig-check 前置）** |
| **Cascadeur AutoPosing / Reallusion AccuRig / Sorceress Rig** | 商业 | 2026 自动绑骨对比中表现好；付费 |
| **RigNet**（SIGGRAPH 2020，开源） | 神经绑骨 | 学术基线，质量可控但工程化成本高 |
| **Auto-Rig Pro**（Blender 插件） | 商业 | Blender 内一键绑骨，生态成熟 |
| 动作：Mixamo 动作库 / 手 K / **SCAIL2**（ComfyUI 视频动作迁移）/ PoseCap 类视频动捕（MediaPipe/OpenPose→BVH） | 混合 | 与 2D 线同套动作方法论 |

### 2.4 进引擎
- Godot 4.x：GLB/glTF 原生支持 + AnimationPlayer；与 2D 线共用 demo 工程
- 备选：Blender→GLB→Godot 程序化导入（export-godot.py 已有 2D 基础，可扩展 3D）

---

## 3. 本机资源评估
- GPU：RTX 4060 8GB（CUDA 可用，见 plan-spine-rig-a.md）
- 可跑：TRELLIS 2 低显存 512³（8GB）；Hunyuan3D 2.1 形状生成（6GB）
- 不可本地跑：Hunyuan3D 全量纹理（16GB）、TRELLIS 2 高质 1024-1536（16-24GB）→ 走 Tripo API 或云端
- 磁盘/网络：模型下载量大（TRELLIS2 ~10GB 级、Hunyuan3D ~20GB 级），需确认磁盘余量；huggingface 不可直连时用 HF_ENDPOINT=https://hf-mirror.com

## 4. 推荐路线（分两级，先 POC 再硬化）

### Tier 1：Tripo API 快速 POC（0.5-1 天，验证全链路）
```
F1 生成：Tripo image-to-3D（试用 key，PBR 纹理，Turbo 模式）→ GLB
F1.5 检查：Tripo /animations/rig-check 确认可绑骨
F2 修正：Blender 减面/UV（DCC-MCP 自动化）
F3 绑骨：Tripo /animations/rig（UniRig 服务化）或 Mixamo 上传自动绑骨
F4 动作：Mixamo 动作库 / 手 K / SCAIL2 迁移
F5 引擎：GLB 导入 Godot（AnimationPlayer 播放）
验收：一个 3D 角色进 Godot 可摆姿势/播放动作；记录每环节耗时
```

### Tier 2：本地开源质量对照（2-3 天，可选）
```
TRELLIS 2：ComfyUI 低显存模式（512³）→ GLB（质量 9/10 级，慢）
Hunyuan3D 2.1：形状生成（6GB）→ 纹理缺失 → Blender 补 UV/贴图 或 用 Tripo texture 端点补
对照指标：纹理保真 / 拓扑质量 / 面数 / 耗时 / 成本
```

### 决策建议
- 3D 线当前**非主线**，2D 骨骼（A 路线）优先；3D 仅在 2D 阻塞窗口期推进 POC
- POC 用 Tier 1（快、可量化），产出对照表后决定是否硬化 Tier 2

## 5. 任务拆解（可勾选进度）

### F1 生成
- [ ] F1-1 确认 Tripo 试用 key 额度（env/key-access.md）
- [ ] F1-2 Tripo image-to-3D（艾琳立绘为输入图）→ GLB + PBR 贴图
- [ ] F1-3 本地对照：TRELLIS 2 ComfyUI 低显存 512³ 生成（HF_ENDPOINT=hf-mirror.com）
- [ ] F1-4 生成质量对照表（纹理/拓扑/面数/耗时/成本）

### F2 修正
- [ ] F2-1 Blender 减面 + UV 重构 + 法线传递（DCC-MCP 自动化脚本）
- [ ] F2-2 贴图检查（PBR basecolor/normal/roughness 完整）

### F3 绑骨
- [ ] F3-1 Tripo rig-check + /animations/rig（UniRig）或 Mixamo 自动绑骨
- [ ] F3-2 蒙皮验证（顶点权重合理、无穿模）

### F4 动作
- [ ] F4-1 Mixamo 动作库套用（idle/walk/attack）或手 K
- [ ] F4-2 （可选）SCAIL2 视频动作迁移对照

### F5 引擎
- [ ] F5-1 GLB 导入 Godot + AnimationPlayer 播放
- [ ] F5-2 验收：一个 3D 角色进 Godot 可动（沿用 audit 记录）

## 6. 风险与对策
| 风险 | 对策 |
|---|---|
| Tripo key 额度耗尽 | 记录额度（env/key-access.md）；转 Meshy 或本地 TRELLIS2 |
| 8GB 显存跑不动高质 | 低显存 512³ / 256³；高质走 API |
| huggingface 不可直连 | HF_ENDPOINT=hf-mirror.com；分步下载 |
| 生成模型拓扑差（面数爆炸/UV 乱） | Blender 减面/UV 重构标准流程；DCC-MCP 自动化 |
| 绑骨失败（非人形/风格化） | UniRig 支持幻想角色；Mixamo 对标准人形最优；备选手绑 |
| 动作"反人类" | 12 原则 + vision 挑刺验收（复用 2D 线方法） |

## 7. 决策记录
- 2026-08-18：重新调研完成，推荐「Tripo API POC + TRELLIS2/Hunyuan3D 本地对照」；3D 线后置，2D 骨骼优先
- 本机 8GB 显存：TRELLIS2 低显存可跑；Hunyuan3D 全量需 16GB 走 API

## 8. 关联文档
- spec/pipeline-unified-2d3d.md（3D 管线对照网易缺口，旧基线）
- spec/dev-roadmap-2d3d.md（P2-3D 阶段任务）
- env/key-access.md（Tripo 等 key 额度）
- env/runtime/tools/（ComfyUI 已部署，可接 TRELLIS2 节点）