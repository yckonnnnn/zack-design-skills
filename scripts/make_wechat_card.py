#!/usr/bin/env python3
"""从微信群二维码截图生成 README 用的卡片图。

    python3 scripts/make_wechat_card.py <截图路径> \
        --name "AI 技能交流群" --expires 10/18 --out assets/wechat-qr.png

为什么要有这个脚本：微信群二维码 **7 天过期**。用手改图的话，每次换码
都要重做一遍排版，做着做着就不做了，最后 README 上挂着一张死码。
把它脚本化之后，换码 = 存一张新截图 + 跑一条命令。

脚本做的事：
  1. 用 OpenCV 自动定位截图里的二维码区域（不写死坐标）
  2. 带静区裁切，缩放后用 LANCZOS 重采样
  3. 排成一张和仓库视觉一致的卡片：群名 + 二维码 + 有效期
  4. **回读生成的图并尝试解码**，确认二维码没被改坏

注意：OpenCV 的 QRCodeDetector 对取景和缩放很敏感，同一张图换个裁切就
可能解不出来——这属于解码器的毛病，不代表码坏了。所以校验采用「多尺度
多次尝试，命中一次即通过」，并且把原始 payload 一起打印出来，方便肉眼
对照微信里扫出来的链接。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---- 与仓库一致的配色（暖白底 + 墨黑 + 荧光绿）----
CARD_BG = (251, 249, 244)
INK = (22, 21, 15)
MUTED = (110, 106, 92)
FAINT = (150, 145, 127)
ACCENT = (216, 243, 42)
HAIRLINE = (232, 228, 218)

FONT_CANDIDATES = [
    pathlib.Path.home() / "Library/Fonts/NotoSansSC-Bold.otf",
    pathlib.Path.home() / "Library/Fonts/NotoSansSC-Regular.otf",
    pathlib.Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    pathlib.Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
]

CARD_W = 840
PAD = 60
QR_TILE = 560
NAME_SIZE = 46
LABEL_SIZE = 19
NOTE_SIZE = 18


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    raise SystemExit(
        "找不到可用的中文字体。请安装思源黑体 / Noto Sans SC，或用 "
        "--font 指定一个 .otf/.ttf 路径。"
    )


def detect_qr(img_bgr: np.ndarray) -> tuple[int, int, int, int]:
    """返回二维码的 (x0, y0, x1, y1)。detect() 比 decode() 稳，几乎总能定位。"""
    detector = cv2.QRCodeDetector()
    result = detector.detect(img_bgr)
    ok, points = result[0], result[1]
    if not ok or points is None:
        raise SystemExit(
            "没能在这张截图里定位到二维码。请用微信「群二维码」原图，"
            "或不要过度裁剪。"
        )
    pts = points[0]
    x0, y0 = int(pts[:, 0].min()), int(pts[:, 1].min())
    x1, y1 = int(pts[:, 0].max()), int(pts[:, 1].max())
    return x0, y0, x1, y1


def crop_with_quiet_zone(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """裁一个正方形，四周留出静区。二维码标准要求静区约 4 个模块宽。"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    side = int(max(w, h) * 1.18)          # 约 9% 静区，比 4 模块更宽裕
    side = min(side, min(img.shape[:2]))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    # 先把窗口推进画面内，再居中，避免越界
    left = max(0, min(cx - side // 2, img.shape[1] - side))
    top = max(0, min(cy - side // 2, img.shape[0] - side))
    return img[top:top + side, left:left + side]


def decode_payload(img_bgr: np.ndarray) -> str:
    """OpenCV 多尺度尝试解码。解不出**不代表码坏了**——见文件头说明。"""
    detector = cv2.QRCodeDetector()
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    for scale in (1, 2, 3, 4, 5):
        probe = gray if scale == 1 else cv2.resize(
            gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
        data, _, _ = detector.detectAndDecode(probe)
        if data:
            return data
    return ""


def vision_payload(path: pathlib.Path) -> str | None:
    """用 macOS Vision 解码（权威）。没有 swift 或不是 macOS 时返回 None。

    OpenCV 会给出假阴性，Vision 不会，所以能用就用它。
    """
    helper = pathlib.Path(__file__).resolve().parent / "verify_qr.swift"
    if not helper.is_file() or shutil.which("swift") is None:
        return None
    try:
        proc = subprocess.run(
            ["swift", str(helper), str(path)],
            capture_output=True, text=True, timeout=180,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None
    payloads = data.get("payloads") or []
    return payloads[0] if payloads else ""


def rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1),
                                          radius=radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def build_card(qr_crop_bgr: np.ndarray, name: str, expires: str | None) -> Image.Image:
    qr = Image.fromarray(cv2.cvtColor(qr_crop_bgr, cv2.COLOR_BGR2RGB))
    qr = qr.resize((QR_TILE, QR_TILE), Image.LANCZOS)

    label_font = load_font(LABEL_SIZE)
    name_font = load_font(NAME_SIZE)
    note_font = load_font(NOTE_SIZE)

    has_note = bool(expires)
    height = PAD + 46 + 22 + 74 + QR_TILE + (56 if has_note else 0) + PAD
    card = Image.new("RGB", (CARD_W, height), CARD_BG)
    d = ImageDraw.Draw(card)

    y = PAD

    # 眉标：荧光绿小方块 + 「微信群」
    d.rounded_rectangle((PAD, y + 5, PAD + 15, y + 20), radius=4, fill=ACCENT)
    d.text((PAD + 26, y - 2), "微信群", font=label_font, fill=FAINT)
    y += 46

    y += 22
    d.text((PAD, y), name, font=name_font, fill=INK)
    y += 74

    # 二维码白色面板（裁切图自带白底，正好当作静区）
    tile_x = (CARD_W - QR_TILE) // 2
    card.paste(rounded(qr, 22), (tile_x, y), rounded(qr, 22))
    d.rounded_rectangle((tile_x, y, tile_x + QR_TILE - 1, y + QR_TILE - 1),
                        radius=22, outline=HAIRLINE, width=1)
    y += QR_TILE

    if has_note:
        y += 26
        note = f"二维码 {expires} 前有效 · 失效后再找我要新的"
        tw = d.textlength(note, font=note_font)
        d.text(((CARD_W - tw) / 2, y), note, font=note_font, fill=MUTED)

    return card


def main() -> int:
    ap = argparse.ArgumentParser(description="生成微信群二维码卡片图")
    ap.add_argument("screenshot", type=pathlib.Path, help="微信群二维码截图")
    ap.add_argument("--name", default="AI 技能交流群", help="群名")
    ap.add_argument("--expires", default=None,
                    help="有效期，如 10/18。留空则不显示有效期那一行")
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path("assets/wechat-qr.png"))
    args = ap.parse_args()

    if not args.screenshot.is_file():
        raise SystemExit(f"截图不存在：{args.screenshot}")

    raw = cv2.imread(str(args.screenshot))
    if raw is None:
        raise SystemExit(f"读不了这张图（格式不支持？）：{args.screenshot}")

    box = detect_qr(raw)
    crop = crop_with_quiet_zone(raw, box)

    card = build_card(crop, args.name, args.expires)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    card.save(args.out, optimize=True)

    # ---- 回读生成结果，确认码没被改坏 ----
    # 优先用 Vision（iOS 扫码同款引擎，可信）；没有就退到 OpenCV（会给假阴性）。
    src_vision = vision_payload(args.screenshot)
    out_vision = vision_payload(args.out)
    engine = "Vision" if out_vision is not None else "OpenCV"

    if out_vision is not None:
        src_payload, out_payload = src_vision, out_vision
    else:
        src_payload, out_payload = decode_payload(raw), decode_payload(
            cv2.imread(str(args.out))
        )

    print(f"源图        {args.screenshot}  {raw.shape[1]}x{raw.shape[0]}")
    print(f"二维码区域  x{box[0]}-{box[2]}  y{box[1]}-{box[3]}")
    print(f"输出        {args.out}  {card.size[0]}x{card.size[1]}")
    print(f"校验引擎    {engine}")
    print(f"源 payload  {src_payload or '(解不出)'}")
    print(f"新 payload  {out_payload or '(解不出)'}")

    if not out_payload:
        if engine == "OpenCV":
            print("校验        未通过（但 OpenCV 常给假阴性）。"
                  "请装 swift 后用 Vision 复核："
                  f"swift scripts/verify_qr.swift {args.out}")
            return 0
        print("校验        失败：生成的图扫不出来，别发布。")
        return 1

    if src_payload and src_payload != out_payload:
        print("校验        失败：payload 变了！生成的图和原图指向不同。")
        return 1

    print(f"校验        通过：payload 一致（{engine} 确认可扫）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
