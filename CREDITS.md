# Credits & Third-Party Notices

This repository is **authored, restructured and rewritten by [Zack](https://github.com/yckonnnnn)**.
The skills here are not a repackaging: the rule sets were re-derived, deduplicated, reorganised into a single doctrine, and the judgement calls, thresholds, routing logic, examples and verification steps are original to this pack.

That said, honest attribution matters and some upstream material is licensed in a way that requires its notice to travel with any distribution. This file exists to satisfy that, and nothing else in the repository repeats it.

## Where the ideas came from

This pack was built by reading, testing and then rewriting the ideas in a set of publicly available design skills and references, including:

| Upstream work | Relationship to this pack |
|---|---|
| Anthropic's **Frontend Design / Figma / Figma Implement Design / imagegen** skills (Apache-2.0) | The Figma→code workflow in `zack-figma-to-code` and the anti-template stance in `zack-anti-ai-look` are a rewrite of procedural material from these skills. Apache-2.0 notice retained below. |
| **Emil Kowalski**'s design-engineering writing and open-sourced skills | Source for the motion-reasoning framework in `zack-motion-taste`. Ideas referenced, text rewritten. |
| **Oil UI** skill (MIT) | Shape of the design-review loop in `zack-redesign-audit`. |
| Community "taste / anti-slop / brutalist / minimalist / high-end" frontend skills circulating on X, GitHub and Chinese dev communities | Consolidated and de-duplicated into `zack-anti-ai-look` and `zack-typography-and-color`. Source of several banned-default lists. |
| `awesome-design-md` collections of published brand design systems | Used as a reference for how real published design systems encode tokens. No brand assets are redistributed here. |
| Google **Stitch** design-taste material | Source of the semantic-DESIGN.md idea. |

If you believe your work is represented here in a way that is not properly credited, open an issue and it will be corrected immediately.

## Apache License 2.0 — retained notices

The following components are distributed under the Apache License, Version 2.0. Full text: [`third_party_licenses/Apache-2.0.txt`](third_party_licenses/Apache-2.0.txt).

- `skills/zack-figma-to-code/` — derived from Anthropic's `figma` and `figma-implement-design` skills.
- `skills/zack-anti-ai-look/` — derived in part from Anthropic's `frontend-design` skill.
- `skills/zack-motion-taste/references/` — the "generate one artifact per section" direction is derived from Anthropic's `imagegen` skill family.

Modifications: reorganised, rewritten, thresholds and verification steps added, source-specific tooling removed. No upstream file is redistributed verbatim.

---

# 中文说明

这个仓库的**作者是 Zack**。里面的规则是我重新推导、去重、合并、重写并亲自跑过一遍的，判断标准、阈值、路由逻辑、示例页和验收步骤都是我自己加的。

但有几份上游材料是 Apache-2.0 授权的，**公开分发时必须保留版权声明**，所以这个文件存在。仓库其他任何地方都不会再重复提这件事。

**注意**：把上游作者的名字抹掉直接改名发布，是会被社区扒的，也可能收到 DMCA。真正能让你站住的不是"看起来像原创"，而是这个包里那些别人抄不走的判断标准（比如"首屏标题在 1440px 下超过 2 行就是错的"这种可执行阈值）。所以做法是：**前台作者是我，合规声明放在这个文件里。**
