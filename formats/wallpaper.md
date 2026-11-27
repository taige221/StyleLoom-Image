---
id: wallpaper
name: 壁纸
version: 2
---

# 壁纸

## Layout prompt (English, primary)

For a phone wallpaper, default to portrait 9:16; for a desktop wallpaper, default to landscape 16:9. The user's actual screen dimensions and aspect ratio take priority. With no device cue, use phone 9:16 as an overridable fallback and state that choice briefly. Leave quiet areas appropriate for clocks, icons, or other interface overlays. For a phone lock screen with no specified layout, keep roughly the upper quarter quiet and place the main content in the middle and lower area without deleting specified subjects. Keep identifying features away from edges vulnerable to cropping. Extend the composition as needed, but do not invent locations, weather, people, or events. Do not render a device frame, system interface, clock digits, icons, or text unless requested. The layout does not require landscapes or any particular style. Set dimensions according to the selected model's capabilities, and do not present upscaling as native high-resolution generation.

## 中文参照（不用于拼接）

- 明确手机时默认竖向 9:16，明确桌面或电脑时默认横向 16:9；用户指定的实际屏幕尺寸与画幅优先。
- 没有设备线索时，以手机 9:16 为可覆盖的兜底，并用一句话说明选择，不要求用户每次填写完整参数。
- 按用途为时钟、图标或其他界面遮挡保留简洁区域。用户要求手机锁屏且未指定布局时，上部约四分之一保持安静，主要内容安排在中下部；不能为了留白删去指定主体。
- 关键主体与辨识点避开易裁切的边缘。背景可以延展组织，但新增地点、天气、人物或情节仍需用户依据。
- 不生成手机外框、系统界面、时钟数字、图标或文字，除非用户明确要求。

## 使用边界

壁纸只定义画幅和使用布局，不限定风景内容或特定画风。分辨率与尺寸按当前模型能力设置，不把上采样标为原生高分辨率出图。
