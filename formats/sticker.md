---
id: sticker
name: 表情贴纸
version: 2
---

# 表情贴纸

## Layout prompt (English, primary)

Use a square 1:1 canvas by default and express one clear action or emotion per sticker, keeping the requested subject count and identity. Keep the full subject visible with transparent margin around it; avoid cropping ears, tails, limbs, or essential props. Use a silhouette readable at small sizes. The default is a genuinely alpha-transparent PNG or WebP, unless a solid background or scene is explicitly requested. Do not paint a checkerboard to imitate transparency. Do not add a white backing shape, outline, cut line, packaging, text, or background props unless requested; preserve supplied text and outline requirements. Prepare separate tasks and records for separate stickers rather than combining them into an unrequested display sheet. The format does not require chibi styling or generic faces. If the selected endpoint cannot provide real transparency, resolve that limitation rather than silently returning an opaque background.

## 中文参照（不用于拼接）

- 默认正方形 1:1，单张贴纸呈现一个清楚的动作或表情；主体数量、身份与动作来自用户输入。
- 保持主体完整入镜并留透明边距，避免尾巴、耳朵、手脚或关键道具被裁切；轮廓适合在小尺寸下辨认。
- 默认真实透明背景，选择支持透明通道的 PNG 或 WebP；用户明确要求实色背景或场景时覆盖。检查透明与可见像素，不能绘制棋盘格来代替透明。
- 不默认添加白色底板、描边、裁切线、贴纸包装、文字或背景道具。用户指定的文案与描边按本次要求处理。
- 多张表情应分别组织任务与记录；不把多张独立贴纸擅自拼成一张展示板。

## 使用边界

贴纸不自动改为 Q 版，也不把人物变成相同年龄或表情。当前接口不支持透明输出时应说明限制并处理取舍，不静默返回不透明底。
