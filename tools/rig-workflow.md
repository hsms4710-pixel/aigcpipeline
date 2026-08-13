# StretchyStudio 骨骼绑定工作流（tools/rig-workflow.md）

> P1-C「2D 骨骼绑定」：立绘分层 PSD → DWPose 自动绑骨 → 微调 → Live2D 参数 → 导出 Spine 4.0。
> 工具：StretchyStudio（开源 MIT，MangoLion/stretchystudio，原生支持 See-Through PSD）。
> 状态：✅ 已打通端到端（2026-08-14 验证，立绘 + chibi 均完成），自动化脚本见 tools/rig-automation/。

## 一、工具部署（已完成）
- 位置：`env/runtime/tools/stretchy-studio/`
- 依赖：Node v24 + pnpm 9（`pnpm.cmd install`）
- 运行：
  - 一键启动：**双击 `env/runtime/tools/stretchy-studio/start-stretchy.cmd`**
  - 或手动：`node serve-onnx.cjs`（5174，onnxruntime-web 静态资源）+ `pnpm.cmd dev`（5173，主应用）
- 浏览器打开 http://localhost:5173/

### 本地化改造（已做，避免外网依赖）
| 项 | 原配置 | 本地化 |
|---|---|---|
| DWPose ONNX 模型 | huggingface.co 下载 | `public/models/dw-ll_ucoco_384.onnx`（134MB，hf-mirror 已下载） |
| onnxruntime wasm | cdn.jsdelivr.net | `serve-onnx.cjs` 静态伺服 node_modules/onnxruntime-web/dist（5174） |
| 源码改动 | `src/io/armatureOrganizer.js` | `wasmPaths='http://localhost:5174/'`；`DWPOSE_URL='/models/dw-ll_ucoco_384.onnx'` |

> 注意：Vite 禁止从 `/public` 动态 import JS 模块，故 wasm/mjs 必须走独立静态服务器（5174）。

## 二、标准操作流程（拖 PSD 后）
1. **Review Layer Mapping**：自动识别图层 tag。我们的 `char_ailin_v10_layered.psd` 18/18 全匹配。
   - 勾选 "Split merged parts (recommended)"（手/脚/眉/眼等自动拆 -l/-r）
   - 勾选 "Mesh all parts after import"（Spine 导出需要 mesh 顶点）
   - 点 **Continue →**
2. **Reorder Layers**：检查层顺序（前发在最上）。点 **Next: Adjust Joints →**
   - 注：legwear 提示 "could not separate" 属正常（单连通形状，不拆）
3. **Adjust Joints**：此处已用 bounding-box 启发式生成初始骨架（黄色关节点可拖拽微调）。
   - 点 **AI Auto-Rig (DWPose)** → **Download**（加载本地模型，134MB 首次加载约 8s）
   - 自动绑骨完成后回到 Adjust Joints，骨架按 DWPose 关键点重排
4. **微调关节**：拖黄色点修正错位（肩/肘/髋/膝）。
5. **Next: Setup Parameters →**：Live2D 参数面板（Angle/Eye/Brow/Mouth/Body/Breath 滑块）。点 **Done →**
6. 主编辑器：可摆姿势（选骨骼旋转）、参数滑杆动表情、Timeline 做动画。

## 三、导出
- 顶部工具栏 **下载图标（Export frames）** → Type 选 **Spine (4.0+)** → **Export**
- 产物：`spine_export.zip` = `skeleton.json`（Spine 4.0 JSON，13 bones/25 slots/mesh 顶点/Idle+Parameters 动画）+ `images/*.png`（26 张 1024×1024 全画布部件贴图）
- 导入 Spine 编辑器：`Spine 菜单 → Import Data... → 选择 skeleton.json`
- 游戏引擎接入：Spine runtime（Godot 用 `spine-godot` / 2dguru 社区版）
- 另可导出 Live2D：Type 选 Live2D Project（.cmo3）或 Live2D Runtime（.moc3 zip）

## 四、自动化冒烟脚本（tools/rig-automation/）
| 脚本 | 作用 |
|---|---|
| `smoke.cjs` | 页面加载 + PSD 拖入 + 图层匹配检查（应 18/18） |
| `rig3.cjs` | 完整绑骨流程（Continue→Adjust→AI Auto-Rig→Download→等 DWPose 完成） |
| `e2e-spine.cjs` | 全流程 + Live2D 参数 + Done + 导出 Spine ZIP 到 assets/demo/char_ailin_rigged/ |

运行：`node <script>.cjs`（需本地 5173/5174 已启动）

## 五、当前产物
- 立绘导出：`assets/demo/char_ailin_rigged/spine_export.zip`（3.2MB，13 bones/25 slots，Idle+Parameters 动画）
- chibi 导出：`assets/demo/char_ailin_chibi_rigged/front_b_spine.zip`（3.4MB，18 bones/25 slots，25 图）
- chibi 拆层源：`assets/demo/char_ailin_chibi_v4/layered/front_b.psd`（See-Through blockswap，1280x1280，17 层）
- 输入源：`assets/demo/char_ailin_v10/layered/char_ailin_v10_layered.psd`（See-Through 拆层 18 层）

## 六、后续（P1-D 动画 / P1-E 引擎）
- Godot 接入：spine-godot 运行时加载 skeleton.json + atlas
- 动画：在 StretchyStudio Timeline 做 idle/walk/attack/hurt 关键帧再导出
- 表情：用 Live2D 参数滑块在 Timeline 打关键帧（happy/sad/angry/neutral 参数过渡）
