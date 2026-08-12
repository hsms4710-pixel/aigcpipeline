# P1 Spec：角色形象 + 语音生成工作台（MVP）

> 状态：**规划中（即将进入开发）** ｜ 对应 ROADMAP Part 1

## 1. 目标
本地 Web 工作台：用户输入**人设卡（JSON）+ 可选参考图/参考音** → 生成**角色立绘（2-4 表情差分）+ 3 句台词克隆语音** → 产出**标准资产包**（PNG 图集 / WAV+字幕 / 人设 JSON / metadata）可下载、可被 Godot 等引擎导入。

## 2. 非目标（第一版不做）
- 不做 3D 生成（glTF 作为 P1 扩展，后置）
- 不做 P2 过场 / P3 Agent / P4 引擎运行时（各有独立 part）
- 不做 P5 评测功能（后置）
- 不做在线多人/云平台，先本地单机

## 3. 输入/输出契约
### 输入
- `persona.json`（人设卡 v0）：名字/种族/职业/性格标签/文风/参考描述/台词清单(3+句)/情绪标签/可选参考图路径/可选参考音路径
- 参考图：单张全身/半身图（可选）；参考音：5-10s 干声（可选）

### 输出资产包（目录约定）
```
<character_id>/
├── persona.json            # 输入的人设卡（校验后副本）
├── metadata.json           # 生成记录：模型/参数/耗时/显存/成本/seed
├── portrait/
│   ├── full.png            # 全身/半身立绘
│   ├── expressions/        # 表情差分（neutral/happy/sad/angry…）
│   │   ├── neutral.png
│   │   └── ...
│   └── sheet.png           # 表情图集（引擎友好）
├── voice/
│   ├── line_1.wav + line_1.txt（字幕）
│   ├── ...
└── preview.html            # 本地预览页（看图/听音）
```

## 4. 子模块
| 模块 | 职责 | 技术候选 |
|---|---|---|
| 形象生成 | 人设→prompt→生图→表情差分→落盘 | Flux LoRA / SDXL LoRA（首选 Flux，理由见下） |
| 语音克隆 | 参考音→克隆→台词 TTS→WAV+字幕 | GPT-SoVITS（首选）/ CosyVoice / F5-TTS |
| 任务编排 | Job 队列 + 阶段状态机 + 单步重试 | 自研轻量（参考 3dModelGenerator job 轮询） |
| 工作台 Web | 上传→预览→确认→下载 | 本地 Web（FastAPI/Flask + 前端），可选 Streamlit 起步 |

## 5. 开源/论文/产品借鉴清单（已调研）
### 形象一致性
- **CharForge**（GitHub RishiDesai/CharForge）：单参考图训练角色 LoRA + 跨场景一致性生成，人物表生成借鉴 Mickmumpitz Flux character consistency workflow → **工作台"从参考图训 LoRA"直接借鉴**
- **Flux Kontext / RefControl**（HF）：参考图+pose 控制，跨生成保持身份 → 表情差分方案候选
- **PaCo-FLUX.1-dev LoRA**（HF X-GenGroup）：RL 训练的一致性生成框架 → 后续质量提升路线
- pixel_art_characters_lora（HF）：像素风角色 LoRA → 风格化资产候选

### 语音克隆
- **GPT-SoVITS**：5s 零样本克隆 + 少样本微调，WebUI 生态成熟 → 首选
- **CosyVoice**（阿里）：流式低延迟、高音色一致性、方言/情感控制 → 备选
- **F5-TTS**：推理快、MIT 商用友好 → 备选（延迟敏感场景）
- **Fish-Speech**：多语言泛化强 → 备选
- 选型依据：GPT-SoVITS 中文质量+克隆易用性最优，先跑通；保留抽象接口可换后端

### 虚拟人/工作台形态
- **handcrafted-persona-engine / aituber-kit / AITuberKit / prometheus-avatar / aituber-onair**：Live2D/3D 虚拟人 + LLM + ASR + TTS + RVC 栈 → 工作台 UI 与"角色卡"交互可借鉴
- **3dModelGenerator**：job 状态轮询 → 编排层参照
- **studiomi300**：Director Agent + 分镜 streaming 输出 → 后续 P2 参照

## 6. 技术选型（MVP）
| 项 | 首选 | 备选 | 理由 |
|---|---|---|---|
| 生图 base | FLUX.1-dev + LoRA | SDXL + LoRA | 一致性/画质更好；SDXL 显存低 |
| LoRA 来源 | 参考图训（CharForge 流程） | 现成风格 LoRA | 单参考图即可锁定角色 |
| 表情差分 | 同人设 prompt + 表情模板 + seed 控制 | Flux Kontext pose/ref | 先简单后可控 |
| TTS | GPT-SoVITS | CosyVoice / F5-TTS | 中文克隆质量 + 生态 |
| 编排 | 自研轻量队列（SQLite + 状态机） | Temporal（过重） | MVP 不引入重框架 |
| Web | FastAPI + 简单前端 | Streamlit | 阶段预览/单步重试交互更自由 |
| 3D | —（后置） | TripoSR / TRELLIS / Hunyuan3D | P1 扩展，不进 MVP |

## 7. MVP 验收标准（gate）
- [ ] 从 1 张参考图/纯文本人设生成 1 个角色 4 个表情差分，肉眼身份一致
- [ ] 3 句台词克隆语音可播放，音色与参考一致度可接受
- [ ] 资产包结构与 metadata 完整，校验脚本通过
- [ ] 工作台：上传→看到每阶段产物→选择→下载；单阶段失败可重试
- [ ] Godot 最小工程能导入立绘 + 播放语音
- [ ] P1 审计完成（audit/audit-log.md）

## 8. 开放问题
- LoRA 训练 vs 纯 prompt 的一致性上限？（先用 CharForge 流程验证，量化身份一致性）
- 无参考音时 TTS 音色如何选？（预设音色库）
- 表情差分数量/情绪集合定多少？（先 neutral/happy/sad/angry 4 个）
