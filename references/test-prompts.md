# 图像模型与预设测试提示词

用于比较模型、检查预设差异与筛查能力边界。包含 30 个风格用例、18 个能力用例，以及 2 个不出图的理解测试。它们是独立的测试内容，不构成用户角色、场景或默认风格的永久设定。

2026-11-26 历史测试选用 OpenRouter 的 `bytedance-seed/seedream-5-5`。首轮运行 S01、S08、S14、S18、T03、T05、T06、T09 共 8 个用例；后续完整补测复用这 8 张，并通过专门生成的虚构参考素材覆盖 T10—T18。这些历史版本用例已覆盖生成，生成完成本身不代表视觉通过；后续逐项检查及补测结论见验证摘要。没有实际参考图时，T10—T18 不运行，也不把文生图结果标成参考图测试通过。

可随项目分发的实际执行结论见 [验证摘要](test-results.md)。完整图片、逐张提示词和人工检查表保留在本机 `output/seedream-5.5-complete-2026-11-26/`，该目录由 Git 忽略，克隆项目后不要求存在；日常使用无需加载实验产物。

历史生成阶段用户要求图片不进入对话上下文；此后查看权限以当前用户要求为准。默认仍然只保存本地文件，不展示、不调用图片查看工具、不输出 base64。接口、文件格式、尺寸、费用与透明通道可以自动检查；主体、风格、文字、身份及编辑效果由用户查看后判断，先记为“待人工检查”。

## 使用与比较方式

每次只读取当前用例调用的风格文件。执行时只使用下方英文主模板，中文段落仅供核对，不重复拼接。将英文画法规则、用例内容与输出要求合成完整提示词；27、30 先写画法目标，再写适用的观察面组合或转译后的关系锚点，不把字面场景说明重复放在前面。先处理冲突，再调用工具。以下内容模板不是直接替代风格规则的风格名称列表。

- 同一模型比较风格：固定内容、画幅、分辨率与输出格式，只换风格块。
- 不同模型比较：固定最终提示词、参考图及其用途，尽量使用相同尺寸；参数不兼容时如实记录，不能静默改条件。
- 先以 1K、每次一张检查基本表现。通过后再选少数用例比较 2K、不同画幅及原生 JPEG/PNG；不要将上采样算作原生高分辨率生成。
- 不预设所有模型均支持负面提示词字段；需要避免的内容写入主提示词。仅发送端点实际支持的参数。
- 单个用例一次成功只能用于初筛。需要稳定性结论时，再针对该用例重复两到三次，记录每次结果，不挑选最好的一张充当全部结果。
- 如请求失败或费用异常，先查记录，不自动连续重试。没有完成视觉检查时，不计算可用率。

建议人工检查记录：内容约束是否满足、风格核心是否成立、是否存在明显结构错误；有文字、身份、透明底或局部编辑时，分别检查对应要求。关键硬要求失败即记为不通过；视觉精美不能抵消内容错误。

成本按实际返回的 `usage.cost` 累计；没有费用字段时记为未知，不用标价冒充实际消费。每张可用图成本 = 该组全部实际费用 / 通过检查的图片数量。

## 通用提示词骨架

英文主模板：

```text
Task: generate a new image / edit the target image.
Content: the specified subjects, counts, actions, setting, time, weather, and objects.
References: the role of Image 1; the role of Image 2; omit if there are no inputs.
Must preserve: the task's required identity features, clothing, objects, positions, and source content.
Style: incorporate the selected preset's English primary rules; do not load a default style when preserving the source.
Layout: single scene or panels, aspect ratio, framing, subject placement, negative space, or transparency.
Text: quote every required string verbatim in its original language; otherwise omit text.
Avoid: task-relevant errors and conflicting effects.
Edit scope: for edits, state exactly what changes and what remains unchanged.
```

中文参照（不用于拼接）：

```text
任务：生成新图 / 修改目标图。
内容：用户指定的主体、数量、动作、场景、时间、天气与物件。
参考图：图 1 的用途；图 2 的用途……没有参考图则省略。
必须保留：身份特征、服装、物件、位置、原图内容等本次硬要求。
风格：读取所选 type，将完整风格规则合入；保留原图时不加载默认风格。
组织：单幅/分镜，画幅，取景，主体布局，留白或透明底。
文字：逐字列出；不需要文字时明确省略。
避免：与本次任务相关的错误和相互冲突的效果。
修改范围：仅编辑任务填写，说明只改什么、其他哪些保持不变。
```

## S01—S30：固定内容的风格测试

共同内容以用户前面提出的例子为基础，补充共同观看方向以避免电视位置与行为脱节；人物没有固定身份，也不指定关系、性别或服装。这些位置规则只属于测试内容。

英文主模板：

```text
Two people sit on the same sofa watching a show together, with a warm atmosphere.
Use one landscape 4:3 scene, framed in a medium shot that clearly includes both people and the sofa.
Both people look toward the same television in the left foreground; show only its back or side, with its screen facing the sofa. Do not place it behind them. Their hands rest naturally without holding other screens.
Keep exactly two people, without extra people, pets, or new story events. No text, logos, or watermarks.
Apply the complete English primary style rules selected for this case.
```

中文参照（不用于拼接）：

```text
两个人坐在同一张沙发上一起追剧，氛围温馨。
单幅横向4:3，中景清楚呈现两人和沙发。两人共同看向左前景的同一台电视，仅显示电视背面或侧面，屏幕朝向沙发，不放在人物身后。双手自然放置，不拿其他屏幕。
固定为两个人，不增加其他人物、宠物或新情节，无文字、logo或水印。使用本用例选中的英文主风格规则。
```

S29 使用下列抽象内容变体，不能一面要求完全非具象，一面要求人物五官清楚：

英文主模板：

```text
Translate the warm feeling of two people watching a show together on a sofa into an abstract image.
Preserve two adjacent primary groups, a shared horizontal support below them, and their common orientation toward the left. Do not require recognizable facial features, complete bodies, furniture construction, or a literal television.
Use only shapes, colors, gestures, and spatial relationships related to the original content, without adding narrative objects.
Landscape 4:3. No text, logos, or watermarks. Apply the selected preset's complete English primary abstraction rules.
```

中文参照（不用于拼接）：

```text
将“两个人坐在沙发上一起追剧”的温馨感受转化为抽象画面。
保留两个并置主形群、下方共同横向支撑及共同朝左的结构锚点；不要求五官、完整身体、家具构造或具象电视。
仅使用关联原内容的形、色、笔势与空间关系，不增加叙事对象。横向4:3，无文字、logo或水印，采用所选预设的完整英文抽象规则。
```

S30 使用仅含关系锚点的内容块，放在当前 30 英文主风格规则之后。该块对应同一追剧事件，但不重复人物、沙发或电视的字面造型要求：

英文主模板：

```text
Content anchors: two adjacent main families of marks, close enough to feel companionable; one shared lateral passage below them; and a common directional tendency toward image left. Keep the two main groups distinct but related. Express the shared support through overlapping lateral strokes and the common orientation through the paths of marks and gaps.
Preserve a warm, quiet mood without drawing a literal scene. No complete body silhouettes, head circles, anatomical parts, constructed furniture, or recognizable screen outline. No additional subject-like group, narrative object, symbol, text, logo, watermark, or border. Landscape 4:3.
```

中文参照：两个相邻而彼此靠近的主要笔痕组，下方有共同横向笔势，二者共同朝左；用重叠笔势、路径与空隙保留陪伴、支撑和共同朝向，不重复完整人体、头部圆形、器官、家具或屏幕轮廓。保持温暖安静的情绪，不增加主体形群、叙事对象、符号或文字。横向4:3。

| 用例 | 预设文件 | 人工重点检查 |
|---|---|---|
| S01 | [01 自然纪实摄影](../skill/01-natural-documentary.md) | 可信材质与自然受光；没有默认胶片滤镜 |
| S02 | [02 复古彩色胶片](../skill/02-retro-color-film.md) | 胶片颗粒与色彩响应共同成立 |
| S03 | [03 直闪快照](../skill/03-direct-flash-snapshot.md) | 直闪受光与投影；不是只提高亮度 |
| S04 | [04 高反差黑白摄影](../skill/04-high-contrast-monochrome.md) | 灰阶、明暗组织与材质仍可读 |
| S05 | [05 电影剧照质感](../skill/05-cinematic-still.md) | 摄影式光影与叙事焦点；不改变事件 |
| S06 | [06 现代清线赛璐璐动漫](../skill/06-modern-cel-anime.md) | 干净线稿、明确色块、硬边阴影 |
| S07 | [07 柔光渐变动漫](../skill/07-soft-gradient-anime.md) | 渐变塑形与柔光；区别于 S06 |
| S08 | [08 复古日本动漫](../skill/08-retro-japanese-anime.md) | 手绘线、平涂主体、有笔触背景；不乱换年代服饰 |
| S09 | [09 精致 Q 版平涂](../skill/09-chibi-flat-illustration.md) | 比例、表情与辨识点；不统一模板脸 |
| S10 | [10 黑白网点漫画](../skill/10-monochrome-screentone-manga.md) | 墨线、网点与黑块；保持单幅而非擅自分格 |
| S11 | [11 清透水彩](../skill/11-transparent-watercolor.md) | 透明叠色、纸白与水痕；不是透明背景 |
| S12 | [12 钢笔淡彩速写](../skill/12-pen-and-watercolor.md) | 钢笔线与淡彩关系；区别于 S11 |
| S13 | [13 彩铅纸感手绘](../skill/13-colored-pencil.md) | 彩铅排线与纸纹；不是表面颗粒滤镜 |
| S14 | [14 哑光水粉绘本](../skill/14-matte-gouache-storybook.md) | 不透明色块、干刷与统一哑光画面 |
| S15 | [15 油画棒手绘](../skill/15-oil-pastel.md) | 蜡质色痕与宽笔触；区别于彩铅 |
| S16 | [16 水墨淡彩写意](../skill/16-ink-wash-light-color.md) | 笔锋、干湿浓淡与虚实；内容关系仍可理解 |
| S17 | [17 光滑卡通 3D](../skill/17-smooth-cartoon-3d.md) | 光滑曲面与体积；区别于黏土 |
| S18 | [18 哑光黏土手作](../skill/18-matte-clay.md) | 手捏形体、制作痕迹、接触阴影 |
| S19 | [19 毛毡织物手作](../skill/19-felt-textile.md) | 纤维参与形体与边缘；不是毛茸茸滤镜 |
| S20 | [20 分层剪纸纸雕](../skill/20-layered-papercut.md) | 可理解的纸层、剪裁边缘、层间阴影 |
| S21 | [21 低多边形立体](../skill/21-low-poly-3d.md) | 几何切面和分面受光；不是平面多边形贴图 |
| S22 | [22 几何扁平插画](../skill/22-geometric-flat-illustration.md) | 剪影、概括形状和色块；内容保持可辨 |
| S23 | [23 Riso 套色印刷](../skill/23-riso-overprint.md) | 叠印、套色与油墨颗粒共同成立 |
| S24 | [24 硬边丝网版画](../skill/24-hard-edge-screenprint.md) | 硬边、实色色块；区别于 S23 |
| S25 | [25 复古像素插画](../skill/25-retro-pixel-art.md) | 一致像素网格、像素簇与有限色板 |
| S26 | [26 印象主义光色绘画](../skill/26-impressionist-light-color.md) | 断续笔触和有色明暗共同表达光色 |
| S27 | [27 立体主义平面重组](../skill/27-cubist-plane-reconstruction.md) | 同一对象不兼容观察面与错位接缝明确；不是单视角填切面；保留双主体关系 |
| S28 | [28 具象超现实绘画](../skill/28-figurative-surrealism.md) | 不擅自增加梦境对象；本例未授权新增超现实事件 |
| S29 | [29 几何抽象构成](../skill/29-geometric-abstraction.md) | 使用抽象变体；形、色、比例和结构张力 |
| S30 | [30 姿态性抽象绘画](../skill/30-gestural-abstraction.md) | 使用仅关系锚点变体；开放笔痕与空隙建形，不以完整剪影填色 |

S28 的固定内容用例主要检查“不擅自改写内容”的边界，不能作为超现实风格的正向示例。已明确允许悬浮关系时，使用 S28P 英文主模板，并合入 28 的完整英文主风格规则：

```text
Two people sit naturally on the same sofa watching a show together, with a warm atmosphere. The sofa floats approximately half a meter above the indoor floor; all other spatial scales remain normal. This floating relationship is explicitly part of the test. Keep lighting and cast shadows consistent with the floating height.
Landscape 4:3 medium shot, showing both people, the sofa, and the gap below it. Both look toward the same television on the left, with its screen facing them; show only its back or side. No extra people, pets, symbolic objects, text, logos, or watermarks.
```

中文参照：两人自然坐在同一张沙发上一起追剧，沙发悬浮于室内地面上方约半米，其他尺度正常；受光和投影与高度一致，显示两人、沙发及下方间隙，两人朝向左侧同一电视，不增加其他人物、宠物、象征物或文字。

### S27F 简化结构诊断

复杂场景中的重组仍不明确时，可先把下方独立内容块放在当前 27 英文主风格规则之后，检验可见的视角冲突，再回到人物场景。此用例不检验人脸融合，也不代表完整 S27 已通过。

英文主模板：

```text
Exactly one undecorated ceramic jug stands at image left and one closed book at image right, resting on one shared plain support. No people or other objects.
Rebuild the jug with its single opening viewed directly from above and its adjoining body viewed straight on, connected by an offset seam. These orientations must not collapse into a normal three-quarter camera view. Keep exactly one jug and one opening.
Keep the book on the right and the common-support relationship readable while flattening depth. Landscape 4:3. No text, logos, watermarks, decorative frames, or unrelated geometric ornaments.
```

中文参照：一个无装饰陶壶位于左侧，一本合上的书位于右侧，共处同一简洁支撑面，不增加人物或物件。陶壶唯一开口采用正上方观察面，相邻壶身采用正向观察面，通过错位接缝连接，不退回普通三分之四相机视角。保留一壶一开口及左右与共同支撑关系，压缩纵深；横向4:3，无文字或装饰。

检查：同一壶内顶视与正视的观察方向是否明确不兼容、接缝是否连接为一个对象；普通椭圆壶口配正常三分之四壶身，或只增加多边形切面，仍不算通过。

## T01—T09：无需参考图的能力测试

### T01 天气、时间与复杂环境

预设：01。画幅：16:9。

英文主模板：

```text
Natural documentary photography of a wooden cabin on a lakeshore, with a short wooden bridge in front and mountains in the distance.
Use a clear summer midday, dry ground, calm water, and no rain.
Landscape 16:9, with the complete cabin and short bridge visible and distant mountains creating depth.
No people, vehicles, snow, night lighting, puddles, reflections on wet ground, text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
自然纪实摄影。一座木屋位于湖岸，屋前有一座短木桥，远处是山。
夏季晴朗的正午，地面干燥，湖面平静，天空没有降雨。
横向 16:9，木屋和短桥完整入镜，远山形成空间层次。
没有人物、车辆、雪、夜景灯光、积水或湿地倒影；无文字、logo、水印。
```

检查：指定天气与时间、建筑和桥的结构、近中远层次、避免项是否被遵守。

### T02 产品与混合材质

预设：custom，写实产品摄影。画幅：4:3。

英文主模板：

```text
A realistic product photograph of three containers on a wooden table: from image left to right, a transparent drinking glass, a round brushed stainless-steel canister, and a matte white ceramic mug.
Separate all three, keep them similar in size, and show them completely. Fill the glass halfway with clear water.
Use soft side lighting to reveal glass refraction, metal reflection, ceramic diffuse reflection, and wood grain accurately.
Landscape 4:3 with a simple background. No branding, text, decorations, or extra containers.
```

中文参照（不用于拼接）：

```text
一张写实产品摄影：木桌上从左到右依次放置透明玻璃杯、拉丝不锈钢圆罐、哑光白色陶瓷杯。
三个容器彼此分开，尺寸相近，全部完整入镜。玻璃杯中装半杯清水。
柔和侧光，准确呈现玻璃折射、金属反射、陶瓷漫反射以及木材纹理。
横向 4:3，背景简洁；不要品牌、文字、装饰物或额外容器。
```

检查：三个对象的材质是否区分、透明与反射是否合理、是否强行套用卡通 3D。

### T03 数量、左右与遮挡

预设：22。画幅：4:3。

英文主模板：

```text
A geometric flat illustration containing exactly three objects on a light background: a red sphere at image left, a blue cube in the middle, and a yellow cone at image right.
The red sphere is in front of the blue cube, hiding approximately the lower-left quarter of the cube. Leave a gap between the yellow cone and the cube, without overlap.
Place all three on the same horizontal baseline, with similar sizes. Landscape 4:3.
Preserve the specified red, blue, and yellow assignments. No fourth object, text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
一张几何扁平插画。浅色背景中只有三个物体：画面左侧一个红色圆球，中间一个蓝色正方体，右侧一个黄色圆锥。
红球在蓝色正方体前方，遮住正方体左下部约四分之一；黄色圆锥与正方体保持间隔，不发生遮挡。
三个物体均落在同一条水平基线上，大小接近。横向 4:3。
保持红、蓝、黄的指定对应关系，不添加第四个物体、文字、logo 或水印。
```

检查：精确数量、颜色对应、图像坐标左右、遮挡方向、是否添加无关装饰。

### T04 人物动作与手部

预设：06；通过后可换 01 复测。画幅：3:4。

英文主模板：

```text
One standing person in a front-facing medium shot, with both hands fully visible.
The person's own right hand is raised beside their shoulder, palm toward the viewer, with five naturally spread fingers. Their own left hand holds the handle of one plain white cup without writing.
Use a simple background and plausible body proportions and joints. Portrait 3:4.
No extra people, arms, repeated fingers, props hiding the hands, text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
单个人物，站姿，正面中景，双手完整可见。
人物右手举到肩旁，手掌朝向观者，五根手指自然张开；人物左手握着一个无字白色杯子的杯柄。
简单背景，身体比例与关节关系合理。竖向 3:4。
不要多余人物、多余手臂、重复手指、遮手道具、文字、logo 或水印。
```

检查：人物自身左右与画面左右的区别、五指、杯柄握持、四肢数量与连接。

### T05 中文标题与逐字排版

预设：14。画幅：3:4。

英文主模板：

```text
A diary cover in matte gouache storybook style. In the lower half, two people sit on a sofa watching a show together.
Reserve a clean title area above them and render only these two Chinese lines, in exactly this order and spelling:
Line 1: 今天也很喜欢你
Line 2: 一起追剧的小日子
Use clear, well-formed characters and comfortable line spacing. Do not translate or transliterate these strings. Add no other characters, letters, numbers, logos, or watermarks.
Portrait 3:4. Keep the title and people from obscuring one another.
```

中文参照（不用于拼接）：

```text
一张哑光水粉绘本风格的日记封面。画面下半部是一张沙发，两个人坐在沙发上一起追剧。
上方留出整洁的标题区域，只出现以下两行中文，顺序和字词完全一致：
第一行：今天也很喜欢你
第二行：一起追剧的小日子
字形端正清晰，行距舒适，不加入其他字、字母、数字、logo 或水印。
竖向 3:4，标题与人物互不遮挡。
```

检查：逐字准确、额外字符、两行顺序、文字遮挡；不能仅以“像中文”算通过。

### T06 四格叙事与角色一致

预设：06。画幅：1:1，2×2 四格。

英文主模板：

```text
A humorous four-panel comic in modern clean-line cel-shaded anime style. Use a square canvas with exactly four panels in a 2x2 grid, read top left, top right, bottom left, bottom right.
The same orange-and-white short-haired cat appears throughout: orange crown and back, white muzzle and chest, and a white tail tip. Keep these markings consistent.
Panel 1: the cat looks at one small piece of fish on the table without touching it.
Panel 2: the cat reaches out a front paw and quietly pulls the fish closer.
Panel 3: the cat has just finished eating the fish; its original place on the table is empty.
Panel 4: the cat sits upright as if nothing happened, with a small fish crumb beside its mouth.
Each panel contains only this one cat, without people, extra fish, or new story events.
No dialogue, titles, sound effects, panel numbers, logos, or watermarks. Use clear gutters between panels.
```

中文参照（不用于拼接）：

```text
现代清线赛璐璐动漫风格的搞笑四格漫画，正方形画幅，明确的 2×2 四格，阅读顺序为左上、右上、左下、右下。
同一只橘白短毛猫，头顶和背部橘色，口鼻与胸前白色，尾巴末端白色；这些花色在四格一致。
第一格：猫看着桌上的一小块鱼，尚未碰到鱼。
第二格：猫伸出前爪，把鱼悄悄拨向自己。
第三格：猫刚把鱼吃完，原来放鱼的位置已经空了。
第四格：猫端坐，装作若无其事，嘴边留着一点鱼屑。
每格只有这一只猫，不出现人，不增加鱼或其他情节。
不用对白、标题、拟声字、编号、logo 或水印。分格之间有清楚留白。
```

检查：恰好四格、阅读顺序、时间进展、鱼的状态、花色一致、没有擅自增加文字。

### T07 封面留白

预设：11。画幅：3:4。

英文主模板：

```text
A transparent-watercolor diary cover showing one gray-and-white short-haired cat asleep, curled beside a window.
Concentrate the cat and window-side content in the lower half. Reserve approximately the upper third as a continuous, quiet, pale area for a title to be added later.
Portrait 3:4, with natural paper white and watercolor washes. Do not generate titles, text, symbols, logos, or watermarks.
No extra animals, people, or decorative objects.
```

中文参照（不用于拼接）：

```text
清透水彩日记封面，一只灰白短毛猫蜷睡在窗边。
猫与窗边内容集中在画面下半部，上方约三分之一保留连续、安静、浅色的留白，供后续排标题。
竖向 3:4，纸白与水彩晕染自然，不要实际生成任何标题、文字、符号、logo 或水印。
不添加其他动物、人物或装饰物。
```

检查：可用留白面积、内容布局、纸白不等于透明通道、无擅自文字。

### T08 手机壁纸与裁切

预设：20。画幅：9:16。

英文主模板：

```text
A layered-papercut phone wallpaper containing one mountain, a lake at its foot, and one tree on the lakeshore.
Portrait 9:16. Place the important tree and lake detail in the middle and lower area, leaving roughly the upper quarter as simple sky for a phone clock.
Keep the tree crown, trunk, and essential shoreline inside the frame, away from the edges.
Show distinct paper layers and shadows between them. Do not add a sun, moon, clouds, people, text, device frame, or watermark.
```

中文参照（不用于拼接）：

```text
分层剪纸纸雕风格的手机壁纸，一座山、山脚一片湖水、湖岸一棵树。
竖向 9:16，树和湖的主要细节放在中下部，上方约四分之一为简洁天空，留给手机时钟。
树冠、树干和湖岸关键部分均在画内，不贴紧边缘。
纸层与层间阴影明确；不添加太阳、月亮、云、人物、文字、手机框或水印。
```

检查：长画幅布局、主体裁切、顶部留白、无手机界面或新增对象。

### T09 透明底贴纸

预设：09。画幅：1:1。参数：`background: transparent`、`output_format: png`。

英文主模板：

```text
One refined chibi flat-color sticker of an orange-and-white short-haired cat sitting and raising one front paw in a happy greeting.
Show only this cat, fully inside the frame, without cropping its tail or raised paw. Leave adequate transparent margin.
Square canvas with a genuinely alpha-transparent background.
No ground plane, background scene, white backing shape, checkerboard pattern, text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
一张精致 Q 版平涂猫咪贴纸：一只橘白短毛猫坐着，抬起一只前爪打招呼，表情开心。
只有这只猫，整体完整入镜，尾巴和抬起的前爪都不裁切，四周保留适量透明边距。
正方形画幅，背景必须是真正透明的 alpha 通道。
不要地面、背景场景、白色底板、棋盘格图案、文字、logo 或水印。
```

检查：文件存在 alpha 且确实含透明像素；主体与边缘是否干净由人工查看。全透明空图不算通过。

## T10—T18：需参考图或修改目标的能力测试

这些用例中的“图 1”等是输入角色说明，执行时必须绑定实际文件，不能原样把未绑定占位符发送给模型。默认仅本地交付的约束仍然有效；未获查看许可时不通过视觉工具读取输入或输出，只使用用户提供的角色说明及文件。

### T10 人物身份与服装解耦

输入：图 1 仅作人物身份参考。预设：06。画幅：3:4。

英文主模板：

```text
Use Image 1 only as the person's identity reference, preserving face shape, hairstyle, age cues, body type, and major identifying features.
Show this person wearing a solid blue crew-neck top, sitting on a park bench and reading a book with a blank cover.
Do not copy the reference clothing, pose, or background, and do not add people.
Modern clean-line cel-shaded anime, portrait 3:4. No text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
以图 1 中的人物作为身份参考，保留其脸型、发型、年龄感、体态及主要辨识特征。
画这个人物穿纯蓝色圆领上衣，坐在公园长椅上读一本无字封面的书。
不要沿用参考图中的服装、动作和背景，也不要添加其他人物。
现代清线赛璐璐动漫，竖向 3:4，无文字、logo 或水印。
```

检查：身份保留与新衣服均成立，参考背景没有泄漏进结果；不以像同类人物代替像同一人物。

### T11 宠物辨识点

输入：图 1 仅作宠物外形参考；用户补充必须保留的花色清单。预设：14。

英文主模板：

```text
Use the pet in Image 1 as the sole subject reference. Preserve the user-listed positions and boundaries of its markings, face and ear shapes, body type, and tail features.
Show it lying on its side on a light-colored cushion, relaxed, with its face and principal identifying markings visible.
Matte gouache storybook style, landscape 4:3. The reference pose, background, and accessories are not fixed requirements.
Do not add another pet, people, text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
以图 1 中的宠物作为唯一主体参考，保留用户列出的花色位置、边界、脸型、耳形、体型及尾部特征。
画它侧躺在一张浅色垫子上，露出脸和主要辨识花纹，神态放松。
哑光水粉绘本风格，横向 4:3。原图姿势、背景与配饰不是固定设定。
不添加第二只宠物、人物、文字、logo 或水印。
```

检查：逐项核对花色，而非只判断物种或毛色相近。具体花纹清单必须随实际参考补齐。

### T12 只参考画风

输入：图 1 仅作画风参考。风格：custom。画幅：4:3。

英文主模板：

```text
Use Image 1 only for its rendering method, linework, color relationships, materials, and lighting treatment; do not copy its subjects, objects, or composition.
The new content is one red ceramic cup and one closed white book on a wooden table. The cup is to the left of the book, with a gap between them.
Landscape 4:3. Do not import extra reference content. No text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
图 1 仅用于参考绘制方式、线条、色彩关系、材质和光影处理，不复制其中的主体、物件或构图。
新内容是：木桌上一个红色陶瓷杯和一本闭合的白色书，杯子在书的左边，两者分开。
横向 4:3，不加入参考图里的额外内容，无文字、logo 或水印。
```

检查：画风迁移与主体独立；不能只靠相似色调算通过。

### T13 只参考构图

输入：图 1 仅作构图参考。预设：18。

英文主模板：

```text
Use Image 1 only for viewpoint, framing, subject scale, and foreground, middle-ground, and background arrangement. Do not copy its style, identity, or objects.
Replace the subject with one sitting orange-and-white cat, preserving the subject position and orientation of the reference layout.
Use a matte handmade-clay style while keeping the cat's species features. No extra characters or text.
```

中文参照（不用于拼接）：

```text
图 1 仅用于参考视角、取景、主体占画比例及前中后景布局，不沿用其画风、人物身份和物件。
将主体替换为一只坐着的橘白猫，保持参考布局中主体的位置和朝向。
使用哑光黏土手作风格，保持橘白猫的物种特征，不添加其他角色或文字。
```

检查：构图和画风两条条件同时成立。执行前确认替换为猫后原布局仍然合理；不合理时先调整用例。

### T14 多图分工与不串用

输入：图 1 人物身份；图 2 外套款式和颜色；图 3 场景与构图。预设：07。

英文主模板：

```text
Use the person's identity from Image 1, dress them in the jacket from Image 2, and place them in the scene from Image 3.
Image 1 supplies only face shape, hairstyle, age cues, and body type. Image 2 supplies only the jacket's color, material, cut, and details. Image 3 supplies the scene, viewpoint, and subject position.
Do not transfer an identity from Image 2 or the clothing and background from Image 1.
The person stands naturally at the subject position in Image 3, with perspective, scale, and lighting coherent with that scene.
Unify the result as soft-gradient anime. No extra people, text, logos, or watermarks.
```

中文参照（不用于拼接）：

```text
使用图 1 的人物身份，穿图 2 的外套，放入图 3 的场景中。
图 1 只提供脸型、发型、年龄感与体态；图 2 只提供外套的颜色、材质、版型和细节；图 3 提供场景、视角和主体位置。
不要把图 2 的人物身份带入结果，不沿用图 1 的衣服和背景。
人物在图 3 的主体位置自然站立，透视、比例和受光与场景一致。
最终统一为柔光渐变动漫画法，不增加其他人物、文字、logo 或水印。
```

检查：三种角色是否串用，身份、服装、场景是否分别正确，拼合是否协调。

### T15 只改颜色

输入：图 1 修改目标，须有一个无歧义的杯子。风格策略：preserve-source。

英文主模板：

```text
Change only the color of the cup body and handle in Image 1 to solid blue.
Keep its shape, position, size, material, and illumination unchanged.
Preserve every other object, the background, composition, visual style, and original text. Add nothing.
```

中文参照（不用于拼接）：

```text
只把图 1 中杯身的颜色改成纯蓝色，杯柄随杯身改色。
杯子的形状、位置、大小、材质与受光保持一致。
其他物件、背景、构图、画面风格和原图文字全部保持不变，不添加内容。
```

检查：局部改色、材质保留、未要求区域是否漂移；不能以整图重画得更漂亮算通过。

### T16 只改天气和光照

输入：图 1 修改目标，选择含建筑、路面与天空的白天户外图。风格策略：preserve-source。

英文主模板：

```text
Change the sunny weather in Image 1 to overcast rain, with cloudy sky and wet pavement showing plausible reflections.
Keep architecture, object counts and positions, identities and clothing, camera angle, and framing unchanged.
Adjust only the lighting, shadows, and reflections required by the weather change. Do not turn it into night or add umbrellas, vehicles, people, or signs.
Preserve the source's visual style and text.
```

中文参照（不用于拼接）：

```text
把图 1 的晴天改成阴雨天气，天空变为阴云，路面湿润并形成符合现场的反射。
建筑结构、物件数量与位置、人物身份和服装、相机角度与取景保持一致。
仅根据天气变化调整必要的受光、阴影和反射，不改为夜晚，不添加伞、车辆、人物或新招牌。
保留原图的表现风格与文字。
```

检查：允许变化和必须保留项的边界、反射合理性、无擅自雨伞等新增内容。

### T17 移除与补全

输入：图 1 修改目标，必须确实含一排五个杯子。风格策略：preserve-source。

英文主模板：

```text
Remove only the second cup from image left in Image 1, together with its own cast shadow and reflection. Reconstruct the background behind it naturally.
Keep the remaining four cups unchanged in count, color, position, size, and spacing. Do not move them to fill the gap.
Preserve the aspect ratio, camera angle, lighting, background, source style, and text.
```

中文参照（不用于拼接）：

```text
只移除图 1 中从画面左边数第二个杯子，同时移除属于它的投影与反射，自然补全后方背景。
其余四个杯子的数量、颜色、位置、大小和间距全部保持不变，不移动它们来填补空缺。
画幅、相机角度、受光、背景、原图风格和文字保持不变。
```

检查：选中目标是否正确，投影是否残留，四个保留对象是否移位或变形。

### T18 整体换画风、保留内容

输入：图 1 修改目标。预设：12。

英文主模板：

```text
Restyle all of Image 1 as a pen-and-watercolor sketch: natural pen lines provide the structure, with light transparent watercolor washes rather than opaque gouache coverage.
Preserve the original subject identities and counts, actions, clothing colors, objects, setting, composition, weather, and existing text verbatim.
Change only the rendering language. Do not add or remove content, landmarks, notes, or decorative borders for a travel-sketch appearance.
```

中文参照（不用于拼接）：

```text
将图 1 整体改为钢笔淡彩速写画法：自然的钢笔墨线承担结构，透明淡彩轻铺，不透明水粉厚涂不作为主要表现。
保留原图主体身份与数量、动作、服装颜色、物件、场景、构图、天气和原有文字内容。
只改变绘制语言，不增删内容；不要为了旅行速写观感而新增地标、笔记或装饰边框。
```

检查：换风格强度与内容保留是否兼得，不能用只叠纸纹或滤镜代替重新表现。

## B01—B02：理解与冲突测试，不调用绘图

- B01 输入“用清透水彩做一张透明底头像”。应选择 11，并单独设置真实透明输出；不得把水彩纸白当成透明底。若模型不支持所需透明输出，先说明能力限制。
- B02 输入“完全非具象的几何抽象，但必须能清楚认出参考图人物的脸和五官”。应简短询问取舍，不擅自放弃任一硬要求，不先付费生成。

## 首轮交付与待测项

每张实际生成的图片分别保存 `prompt.md`、`request.json`、去除图片数据的 `response-metadata.json`、`record.md` 和原始图片；汇总文件列出费用、耗时、尺寸及人工检查状态。请求文件不包含凭据。

首轮 8 张只验证接口可用性、部分风格和功能的初筛；不代表 30 种风格全部测试通过，不代表人物一致性、参考图迁移或局部编辑已经验证，也不据此宣布性价比胜出。
