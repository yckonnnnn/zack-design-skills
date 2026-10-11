#!/usr/bin/env python3
"""Regenerate the example preview screenshots.

Usage:
    python3 scripts/screenshots.py

Requires Playwright with Chromium installed:
    pip install playwright && playwright install chromium

Writes examples/before-after/preview-{before,after,index}[-mobile].png
and exits non-zero if any page scrolls horizontally at any tested width.

已知的残余不确定性（已排查，属无害）
------------------------------------
为了防止「每跑一次就产生一堆无意义的图片 diff」，脚本做了两件事：

1. 冻结动画与过渡（before.html 有个无限循环的跑马灯，index.html 又把
   before/after 装进 iframe，所以必须用 add_init_script 注入到每个 frame）
2. 等所有 frame 加载完 + 字体就绪 + 两帧绘制，而不是死等固定毫秒

做完之后 6 张图里 5 张完全确定。**preview-index.png 仍有约 1/7 的概率
产生差异**：实测差异只有 10 个像素（共 1,296,000 个），每通道偏差 ≤5/255，
集中在右侧 iframe 的左边缘 42×4px 区域，肉眼完全看不出。

已确认这不是本脚本或页面代码的问题（量化缩放比、冻结动画、延长等待都
试过），而是 Chromium 对缩放的 iframe 做栅格化时本身存在微小不确定性。
继续追下去收益极低，故记录于此。
"""

from __future__ import annotations

import pathlib
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    print("playwright is not installed — run: pip install playwright && playwright install chromium")
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parent.parent
EX = ROOT / "examples" / "before-after"

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
WIDTHS = (1440, 1024, 768, 390)


def main() -> int:
    failures: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for page_name in ("before", "after", "index"):
            src = EX / f"{page_name}.html"
            if not src.is_file():
                failures.append(f"{src.name}: missing")
                continue

            for label, viewport in (("", DESKTOP), ("-mobile", MOBILE)):
                page = browser.new_page(viewport=viewport, device_scale_factor=1)
                errors: list[str] = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                # 冻结动画与过渡再截图。before.html 有个无限循环的跑马灯，
                # 不冻结的话每次截到不同相位，预览图每跑一次就变一个样，
                # 每次提交都会带上一堆无意义的图片 diff。
                #
                # 必须用 add_init_script 而不是 add_style_tag：index.html 把
                # before/after 装在 iframe 里，而 add_style_tag 只作用于主框架，
                # iframe 内部的跑马灯照样在动。init script 会注入每个 frame。
                page.add_init_script(
                    "document.addEventListener('DOMContentLoaded',()=>{"
                    "const s=document.createElement('style');"
                    "s.textContent='*,*::before,*::after{"
                    "animation:none !important;transition:none !important}';"
                    "document.head.appendChild(s);});"
                )
                page.goto(src.as_uri())

                # 等到所有 frame 真的加载完、字体就绪、第一帧画完，再截图。
                # 不能只死等一个固定毫秒数：index.html 把 before/after 装在
                # iframe 里，机器一忙（比如连着跑好几轮）iframe 还没排完版就被
                # 截下来，会产出与平时不同的图，同样污染提交 diff。
                for frame in page.frames:
                    try:
                        frame.wait_for_load_state("load", timeout=10_000)
                    except Exception:
                        pass
                try:
                    page.wait_for_function(
                        "() => document.fonts.status === 'loaded'", timeout=10_000
                    )
                except Exception:
                    pass
                try:
                    # 让浏览器确认没有待处理的布局/绘制
                    page.evaluate(
                        "() => new Promise(r => requestAnimationFrame("
                        "() => requestAnimationFrame(r)))"
                    )
                except Exception:
                    pass
                page.wait_for_timeout(600)

                out = EX / f"preview-{page_name}{label}.png"
                page.screenshot(path=str(out))
                print(f"wrote {out.relative_to(ROOT)}  {viewport['width']}x{viewport['height']}")

                if errors:
                    failures.append(f"{src.name}: page errors {errors}")

                for w in WIDTHS:
                    page.set_viewport_size({"width": w, "height": 900})
                    page.wait_for_timeout(200)
                    overflow = page.evaluate(
                        "() => document.documentElement.scrollWidth"
                        " - document.documentElement.clientWidth"
                    )
                    if overflow > 0:
                        failures.append(
                            f"{src.name}: horizontal overflow {overflow}px at {w}px"
                        )
                page.close()

        browser.close()

    if failures:
        print("\nFAILURES")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nall pages render with no horizontal overflow at " + ", ".join(f"{w}px" for w in WIDTHS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
