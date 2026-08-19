# assets/demo/ 产物索引（角色 AIGC → AI NPC → 引擎）

> 更新时间：2026-08-19 ｜ 本文件标记每个 demo 工程与角色资产的【最终版 / 历史版】，避免误用旧资产。
> 规则：新增版本时在此登记；旧版本保留在目录内（可追溯），但标注为历史。

## 1. Godot 工程（可运行 demo）

| 工程 | 内容 | 状态 |
|---|---|---|
| **godot-pokemon-demo/** | **当前俯视 demo**：宝可梦 NDS BW 风，艾琳 4向x4帧 walk，W2.1 地图 v2.4（12格 atlas：3草/2水/沙/土/路 + 村庄6房 + 有机湖/桥/成林树丛），相机跟随。启动 `start-pokemon.cmd` | ✅ 当前主 demo |
| **godot-game-base/** | **2D 横板主游戏**：SunnyLand Forest 地图 + 艾琳侧视帧（像素/HD-2D 双风格）+ 箭矢/跳跃/攻击/落地缓冲 + 战斗。启动 `start-game.cmd` | ✅ 可玩 |
| godot-chibi-anim-hd2d-v2/ godot-chibi-anim-pixel/ | 帧动画演示（B 路线：AI 关键帧 → AnimatedSprite2D） | ✅ B 路线产物 |
| godot-chibi-v2-demo/ godot-char-demo/ godot-import-demo/ godot-topdown-demo/ | 早期角色展示 / 导入验证 / 俯视原型 | 历史 |
| godot-game-base_assets/ | 横板资产源（hero/slug/arrow/tiles/maps/bg） | 素材 |

## 2. 艾琳角色资产版本

| 资产 | 内容 | 状态 |
|---|---|---|
| char_ailin_v10/ | **立绘锚点（最终画风）**：full/bust/4表情/转面 + layered PSD（See-Through 18层） | ✅ 最终 |
| char_ailin_chibi_v4/ | **Q版小人锚点（最终）**：8视图一致，Hero=front_b | ✅ 最终 |
| char_ailin_splash_v9/ | 立绘风格参考（splash 系列最优版） | ✅ 参考 |
| char_ailin_chibi_8dir/ char_ailin_chibi_v2/ v3/ | 8向/早期 Q版迭代 | 历史 |
| char_ailin_m04/ char_ailin_anim/ char_ailin_rigged/ char_ailin_chibi_rigged/ | 骨骼动画产物（FK 帧 / Spine zip / 预览） | ✅ A 路线产物 |
| char_ailin_splash ~ v8 / char_ailin_v2 / char_ailin_ak* / char_ailin / chibi_apose / pixel / style_px / style_attempts | 早期立绘/风格实验 | 历史 |
| godot-char-demo/assets/ | 早期立绘表情 + Q版（exp_*/portrait_*/chibi_*） | 历史（已被 v10/v4 取代） |

## 3. 俯视地图管线（godot-pokemon-demo 配套）

| 产物 | 内容 | 状态 |
|---|---|---|
| **pokemon_map/map_v2.json** | 当前地图数据（v2.4：60x40，瓦片 0-10，trees/flowers/houses/spawn） | ✅ 当前 |
| **a2/overworld_v2/overworld_v6_atlas.png** | 当前瓦片集（12格 4x3：3草×旋转去条纹 + 2水 + 沙 + 土 + 路） | ✅ 当前 |
| a2/overworld_v2/overworld_v3_atlas.png | AI 草地瓦片集（画风 8，有纹理条纹） | 备选 |
| a2/overworld_v2/overworld_v5_atlas.png | 程序化草地瓦片集（无条纹但画风割裂） | 备选/参考 |
| pokemon_map/house.png | 村庄小屋 sprite（A2 生成 + 抠图） | ✅ 使用中 |
| pokemon_map/tiles/overworld.png | 早期 6 瓦片（3草2水1路） | 历史 |
| pokemon_map/tiles_v3/transition.png、closed_loop/tiles_decor/decor.png | 过渡/装饰瓦片（旧版地图用） | 历史 |
| pokemon_map/char_4dir_walk/ | 艾琳 4向x4帧 walk（视觉模型提示词生成，gate 7.0 PASS） | ✅ 使用中 |
| pokemon_map/ailin_pokemon.png / char_4dir/ | 艾琳俯视锚点 / 4 向静态 | ✅ 参考 |
| pokemon_map/*_gate.json | Vision Gate 报告（map v2/v21/v22/v23/v24、walk、style） | 验收记录 |

## 4. A2 流水线产物（assets/demo/a2/）

| 产物 | 内容 | 状态 |
|---|---|---|
| a2/overworld_v2/ | 瓦片集生成闭环：raw.png + prompt.json + gate.json（PASS 7.0）+ manifest.json + frames/ + atlas v3/v5/v6 | ✅ 成功案例 |
| a2/house_pokemon/ | 房子生成（character 门禁 FAIL 3，raw 已抠图 → house.png） | 部分成功 |

## 5. 视觉验收记录（Vision Gate 分数轨迹）
- 瓦片集（overworld_v2）：**7.0 PASS**（风格统一8 / 语义9 / 无缝7 / 像素5）
- 地图全景：旧 3 → v2.2 6 → v2.4 **6**（可玩结构7 / 画风7 / 统一7，条纹消除）
- 游戏内截图：旧 2 → v3 5 → **5**（物件统一7）——未达 7，W2.1 继续
- walk 动画：**7.0 PASS**（帧一致8 / 节奏8）
