# LinkedIn 搜岗（目标地区，近约 30 天）

只负责发现岗位卡片。域级节流与 429 见 [rate-limit-and-pacing.md](rate-limit-and-pacing.md)。分区覆盖与续跑见 [search-coverage.md](search-coverage.md)。填写申请见 [applying.md](applying.md)。中断后续跑见 [queue.md](queue.md)。

## Guest 接口

公开接口，不必带登录 cookie：

```
https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={URL编码的词}&geoId=103291313&f_TPR=r2592000&sortBy=DD&start=0
```

- 必须先有用户确认的投递地区，再代入对应 `geoId`，不要默认香港。
- 地区是香港（Hong Kong / Hong Kong SAR）时，用 `geoId=103291313`。也可以加 `location=Hong%20Kong%20SAR`，但以这个 geoId 为准，避免范围漂到邻近地区。
- 其他地区用 `https://www.linkedin.com/jobs-guest/api/typeaheadHits?query={地名}&typeaheadType=GEO` 查出 geoId，再写入搜索 URL。查不到就停下来问清地点，不要沿用香港 geoId。
- `f_TPR=r2592000` 是近约 30 天；`r86400` 是一天，`r604800` 是一周。首轮存量用 30 天；增量按上次之后的窗口即可（可与旧 backfill 时间窗重叠，用岗位 ID 去重）。
- `sortBy=DD` 表示最新优先。
- 每页大约 10 张卡片；`count` 参数通常被忽略。用 `start=0`、`10`、`20`… 翻页。某一页少于 10 张，且 HTTP 成功，才可将该分区标为 `complete`。
- 返回的是 HTML 片段，不是 JSON。从每个 `<li>` 取出：
  - 岗位 ID：`data-entity-urn="urn:li:jobPosting:(\d+)"`
  - 标题：`h3.base-search-card__title`
  - 公司：`h4.base-search-card__subtitle` 里的链接文字
  - 地点：`span.job-search-card__location`
  - 发布时间：`<time datetime>`
  - 链接：`a.base-card__full-link` 的 href，从第一个 `?` 起去掉跟踪参数
- 规范 JD 链接写成 `https://www.linkedin.com/jobs/view/{job_id}`。跨关键词只用岗位 ID 去重。
- Guest 卡片通常看不出是否有 Easy Apply，不要在这个阶段下结论。

Guest 顶层请求必须遵守 [rate-limit-and-pacing.md](rate-limit-and-pacing.md) 的默认间隔与 10 分钟滚动上限；旧文档里的「≥1 秒」已不够，**不要**在 429 后缩短间隔。同一时刻只进行一个 guest 翻页或 JD 打开。

## 429、截断与已登录回退

实战里常见：部分关键词在翻过若干页后开始 HTTP 429，甚至 36/36 个词都被截断；JD 抓取也会 429。**不能**把不完整覆盖说成「该地区近 30 天的全部岗位」。

收到 429 时：

1. 按 [rate-limit-and-pacing.md](rate-limit-and-pacing.md) 落盘日志、`Retry-After`（若有）、回退与可能的 30 分钟域冷却。
2. 将该 `partition_id` 标为 `truncated` 或 `deferred`，`next_cursor` 停在失败的那一页。
3. 换关键词前至少等待配置的 `min_gap_between_keywords_sec`。
4. 若连续多个词一开始就 429、或 guest 返回 Cloudflare 挑战页，在**用户已授权的已登录**浏览器里，用同样的词、已解析的 geoId 和近 30 天筛选搜岗：`https://www.linkedin.com/jobs/search/?keywords=...&geoId={已解析的geoId}&f_TPR=r2592000&sortBy=DD`。地区是香港时，这里的 geoId 必须是 `103291313`。这是 guest 不可用时的正当主路径或回退，不是为了绕过冷却而换通道。
5. 已登录侧仍被限流或要求验证：停止该路由，告诉用户；不要用多账号、代理或无头模式绕过。

汇报漏斗时列出：`complete` / `truncated` / `deferred` 分区数、各词最后成功的 `start`、以及 429 次数。队列已空 **不等于** 搜索覆盖已完成。

## 读完整 JD

投之前（或标题拿不准时）打开 `https://www.linkedin.com/jobs/view/{job_id}`。岗位说明常常在 `.show-more-less-html__markup`。不要把卡片标题当成已经读完 JD。

岗位页 **HTTP 429、超时、或页面明显不完整/空正文** 时：

- 写入 `deferred.jsonl`，原因如 `jd_fetch_429` / `jd_fetch_timeout` / `jd_fetch_incomplete`。
- 按节流规则安排 `next_retry_at`；**不要**写入 `apply_log.jsonl` 的 `skipped`，**不要**当作最终不投。
- 重试耗尽后仍无法读取：状态保持 `pending`/`deferred`，在分析报告里列为「JD 未解析」；只有用户明确接受遗漏，或后续重试仍证实岗位已关闭，才可用硬规则跳过（见 [selection.md](selection.md)）。

只有标题、且标题无硬性排除时，可暂时保留在发现列表，但投递当时必须再读现场 JD。

## 搜索词

从用户的「优先」和「可考虑」生成多个词，见 [selection.md](selection.md)。每个词独立翻页并落盘分区状态，再用岗位 ID 合并。不要只搜一两个词就声称没有岗。
