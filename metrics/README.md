# metrics/traffic.csv

每天一行，自动记录这个仓库的真实使用情况。

**为什么需要它**：GitHub 的 traffic 接口**只返回滚动 14 天**的数据。不记录，历史就永久丢失了——你会永远不知道第 3 个月有多少人在用。这个目录是唯一的长期账本。

由 [`.github/workflows/traffic-snapshot.yml`](../.github/workflows/traffic-snapshot.yml) 每天 03:17 UTC 自动追加，也可以随时手动触发（Actions → traffic snapshot → Run workflow）。

## 字段

| 字段 | 含义 | 在哪看 |
|---|---|---|
| `stars` | 星标总数 | 仓库页右上角 |
| `forks` | fork 总数 | 仓库页 |
| `watchers` | 订阅数 | 仓库页 |
| `views_total` | 仓库页浏览量（含重复） | Insights → Traffic |
| `views_unique` | 去重访客数 | Insights → Traffic |
| `clones_total` | **克隆次数** | Insights → Traffic |
| `clones_unique` | **去重克隆人数** | Insights → Traffic |
| `release_downloads` | Release 附件下载次数 | Release 页每个附件旁边 |
| `referrers` | 流量来源前 5 名 | Insights → Traffic |

## 三条读数须知

1. **`clones_unique` 是这套指标里最有价值的一个。** 它约等于「有多少人真的把这套技能装进了自己的工具」——这比 star 更接近真实使用。star 可以随手点，clone 要付出行动。
2. **数据有延迟，通常几小时到一天。** 刚推送完看不到数字是正常的，别以为没生效。
3. **只有附加在 Release 上的文件才计数。** Release 页面里自动生成的 `Source code (zip)` 和 `Source code (tar.gz)`，GitHub **不统计下载次数**。所以这个仓库挂了 `zack-design-skills-v1.0.0.zip` 作为附件——那个才是计数入口。

## 手动补录

```bash
cd zack-design-skills
python3 scripts/traffic_snapshot.py
```

同一天重复运行会覆盖当天那一行，不会产生重复数据。

## 如果你想让 TRAFFIC_TOKEN 生效

默认用 Actions 自带的 `GITHUB_TOKEN`。如果日志里出现 403，去仓库 Settings → Secrets and variables → Actions 新建一个 `TRAFFIC_TOKEN`（个人访问令牌，勾 `repo` 权限），工作流会自动改用这个。

---

## 关于「怎么让别人点 star」

有一件事必须说清楚：**clone、fork、下载，都不会给你加 star。** star 只能由人在 GitHub 页面上主动点一下。

所以想让 star 涨，只有三条路：

1. **让仓库能被搜到** —— topics、描述、README 里的关键词（这个仓库已经配了 13 个 topics）
2. **让人 10 秒内看懂价值** —— 所以有在线对比演示页，不用装任何东西就能看到效果
3. **明确说出来** —— 分享链接的时候加一句「觉得有用的话给个 star」。不说，绝大多数人不会点。这不是功利，是基本礼貌：你给了东西，说明你希望得到什么反馈。

分布本身不产生 star，**可被发现 + 有说服力 + 一句明确的请求**才产生 star。
