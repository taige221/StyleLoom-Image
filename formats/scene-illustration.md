---
id: scene-illustration
name: 场景插画
version: 2
---

# 场景插画

与外层选择的完整风格组合，只组织用户给定的主体、动作和环境。

## Layout prompt (English, primary)

Use a single landscape 4:3 scene by default, with the user's dimensions, aspect ratio, and viewpoint taking priority. Frame the specified subjects, actions, and essential relationships clearly without unnecessary cropping. Arrange depth and subject spacing to serve the given content, without adding objects to fill the frame. Derive the background from the request, designated references, or edit target; do not turn unspecified locations, weather, time, clothing, or relationships into fixed settings. Add titles, dates, dialogue, panels, or borders only when requested. Preserve required on-image text verbatim and reserve space for it. This layout can accompany photography, drawing, 3D, craft media, or painting. Set a supported API aspect ratio or size as well as describing the layout in words.

## 中文参照（不用于拼接）

- 默认单幅横向 4:3；用户指定的尺寸、画幅或视角优先。
- 取景以主体、动作和关键关系可读为准，避免不必要的裁切。近中远层次和主体间距服务于已给定内容，不为填满画面而增加物件。
- 背景来自用户描述、指定参考或修改目标；未提供的具体地点、天气、时间、服装与关系不自动补成固定设定。
- 不默认添加标题、日期、对白、分格或边框。用户要求的文字逐字保留，并为它安排位置。

## 使用边界

“场景插画”是用途，不限定二维绘画；可以与摄影、三维、手作和艺术绘画预设组合。精确画幅应使用所选 API 实际支持的参数表达，不能只依赖提示词。
