# assets/

给仓库门面和 README 用的图。

| 文件 | 用途 | 怎么来的 |
|---|---|---|
| `banner.svg` | README 顶部横幅 | 手写 SVG，1200×420 |
| `social-preview.png` | GitHub 分享卡片图 | 由 banner 渲染，1280×640 |
| `wechat-qr.png` | 微信群二维码卡片 | `scripts/make_wechat_card.py` 生成 |

---

## 更新群二维码（每 7 天一次）

微信群二维码**只有 7 天有效期**，这是微信的限制。所以别手改图——用一个脚本重出：

```bash
# 1. 微信里导出新的群二维码，存成一张截图（比如 ~/Downloads/群码.png）
# 2. 一条命令重出卡片
python3 scripts/make_wechat_card.py ~/Downloads/群码.png \
    --name "AI 技能交流群" --expires 10/25
```

脚本会自己定位截图里的二维码、裁切、排版、然后**回读生成结果确认还能扫**。
输出默认写到 `assets/wechat-qr.png`，直接提交推送就行。

### 校验到底可不可信

这一点值得说清楚，因为它踩过坑：

脚本的校验优先用 **macOS 的 Vision 框架**（`scripts/verify_qr.swift`），
也就是 iOS 相机扫码用的同一套引擎，结论可信。

它一开始用的是 OpenCV 的 `QRCodeDetector`，结果发现**这个解码器完全不可靠**——
同一张二维码，换个缩放比例或重采样滤波器就时灵时不灵，毫无规律。它会给出
**假阴性**：生成的图明明好好的，它说解不出来，害你以为码坏了。

所以现在：

- **Vision 可用** → 用它，校验结果算数
- **没有 Vision**（非 macOS，或没装 swift）→ 退到 OpenCV，此时脚本只给
  「参考」结论并明确告诉你**别把 OpenCV 的失败当真**

手动复核任意一张二维码：

```bash
swift scripts/verify_qr.swift assets/wechat-qr.png
# {"ok":true,"payloads":["https://weixin.qq.com/g/..."]}
```

### 如果脚本说定位不到二维码

说明截图的取景不合适。用微信里「群二维码」导出/截图的原始画面，
不要在群公告的合成图里截图，也不要手动裁剪得太紧。

### 换群名或想改排版

配色和字号在 `scripts/make_wechat_card.py` 顶部的常量里，和仓库视觉一致
（暖白底 `#FBF9F4` + 墨黑 `#16150F` + 荧光绿 `#D8F32A`）。改完重跑即可。
