---
id: "25"
type: retro-pixel-art
name: 复古像素插画
group: 图形与印刷
version: 2
status: draft
---

# 25 复古像素插画

由外层 [SKILL.md](../SKILL.md) 选择后按需读取；共享内容约束、图片类型、参考图处理、工具调用与留档规则由外层负责。

## Style prompt (English, primary)

Render the specified content as retro pixel art on one consistent logical pixel grid. Use fixed-size square cells, crisp stepped contours, and deliberately organized pixel clusters to describe form. Model light and materials with a controlled palette and a small number of discrete color steps, preserving the silhouettes, colors, and actions needed for recognition. Keep the same pixel scale across focal subjects, background, texture, and dithering; detail density may vary without changing the grid. Avoid subpixel antialiasing, smooth gradients, blur, interpolated scaling, and mixtures of coarse pixel blocks with fine smooth drawing. Do not add game interfaces, text, health bars, or pixel borders unless requested.

## 中文参照（不用于拼接）

将指定内容表现为遵循统一逻辑像素网格的复古像素插画。采用固定大小的方形单元、清楚的阶梯轮廓与有组织的像素簇建形，以受控色板和少量离散色阶解释光照与材质，保留辨识所需的轮廓、颜色和动作。主体、背景、纹理和抖色使用同一像素尺度，允许细节密度变化而不改变网格。避免亚像素抗锯齿、平滑渐变、模糊、插值缩放及粗像素与细腻平滑绘画混杂；不默认加入游戏界面、文字、血条或像素边框。

## 核心关系

统一逻辑网格、固定像素尺度和受控色阶共同塑造可读形体。

## 使用边界

- 像素是表现方式，不表示交付文件必须使用某种位深或固定尺寸。
- 不默认加入游戏界面、文字、血条或像素边框；生成后检查网格一致性，不能仅凭像素观感认定为严格网格素材；需要放大时使用最近邻整数倍缩放，放大本身不修复原图网格。

