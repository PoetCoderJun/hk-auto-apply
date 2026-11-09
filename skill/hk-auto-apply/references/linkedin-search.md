# LinkedIn 搜岗（香港，近约 30 天）

只负责发现岗位卡片。填写申请见 [applying.md](applying.md)。中断后续跑见 [queue.md](queue.md)。

## Guest 接口

公开接口，不必带登录 cookie：

```
https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={URL编码的词}&geoId=103291313&f_TPR=r2592000&sortBy=DD&start=0
```

- 香港用 `geoId=103291313`（Hong Kong SAR）。查其他地点：`https://www.linkedin.com/jobs-guest/api/typeaheadHits?query={地名}&typeaheadType=GEO`
- 也可以加 `location=Hong%20Kong%20SAR`，但香港海投以这个 geoId 为准，避免范围漂到邻近地区。
- `f_TPR=r2592000` 是近约 30 天；`r86400` 是一天，`r604800` 是一周。首轮存量用 30 天；增量按上次之后的窗口即可。
- `sortBy=DD` 表示最新优先。
- 每页大约 10 张卡片；`count` 参数通常被忽略。用 `start=0`、`10`、`20`… 翻页。某一页少于 10 张，就停止这个关键词。
- 返回的是 HTML 片段，不是 JSON。从每个 `<li>` 取出：
  - 岗位 ID：`data-entity-urn="urn:li:jobPosting:(\d+)"`
  - 标题：`h3.base-search-card__title`
  - 公司：`h4.base-search-card__subtitle` 里的链接文字
  - 地点：`span.job-search-card__location`
  - 发布时间：`<time datetime>`
  - 链接：`a.base-card__full-link` 的 href，从第一个 `?` 起去掉跟踪参数
- 规范 JD 链接写成 `https://www.linkedin.com/jobs/view/{job_id}`。跨关键词只用岗位 ID 去重。
- Guest 卡片通常看不出是否有 Easy Apply，不要在这个阶段下结论。

两次请求之间至少间隔约 1 秒。即使这样，同一个关键词也常常在成功翻过前几页之后返回 HTTP 429。这是常见情况，不是偶发故障。

## 429 和挑战页

实战里：许多关键词在成功翻 2 到 8 页后开始 429，这个词的覆盖会不完整。429 的响应可能是一段跳回 linkedin.com 的 HTML，而不是岗位卡片。

不要对同一个 `keywords + start` 死循环重试。按这个顺序处理：

1. 记下这个关键词已经拿到的页数、卡片数，并标成被截断。
2. 停止继续翻这个词。
3. 稍等再换下一个关键词，不要连续对许多词狂刷。
4. 如果连续多个词一开始就 429，或 guest 返回 Cloudflare 挑战页，改到已登录的浏览器里搜同样的词、地点和近 30 天筛选：`https://www.linkedin.com/jobs/search/?keywords=...&geoId=103291313&f_TPR=r2592000&sortBy=DD`
5. 浏览器也被限流或要求验证时，停下来告诉用户，不要假装已经搜全。

汇报漏斗时如实写哪些词被 429 截断。不要把部分结果说成「香港近 30 天的全部岗位」。

## 读完整 JD

投之前（或标题拿不准时）打开 `https://www.linkedin.com/jobs/view/{job_id}`。岗位说明常常在 `.show-more-less-html__markup`。不要把卡片标题当成已经读完 JD。

抓取岗位页失败时：把该岗记成不投，备注「岗位页读取失败」，不要放进待投队列。只有标题能看、且标题本身没有硬性排除时，可以暂时留着，但投递当时必须再读一遍现场 JD。

## 搜索词

从用户的「优先」和「可考虑」生成多个词，见 [selection.md](selection.md)。每个词独立翻页，再用岗位 ID 合并。不要只搜一两个词就声称没有岗。
