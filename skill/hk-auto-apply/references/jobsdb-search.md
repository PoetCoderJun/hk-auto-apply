# JobsDB 搜岗（香港，近约 30 天）

网站是 `hk.jobsdb.com`。填写申请见 [applying.md](applying.md)。中断后续跑见 [queue.md](queue.md)。顶层翻页节流与覆盖分区见 [rate-limit-and-pacing.md](rate-limit-and-pacing.md) 与 [search-coverage.md](search-coverage.md)。

## 怎么搜

用职位名斜杠路径，例如：

```
https://hk.jobsdb.com/Assistant-Relationship-Manager-jobs
```

把搜索词里的空格换成连字符。按用户的选岗规则生成多个路径，不要只用一两个词。

不要用 `keywords=...&where=All Hong Kong` 这类组合来判断「没有岗」：它常常返回 0 条，但斜杠路径里其实有结果。

时间窗选近约 30 天（页面上的 Date Listed / 30 days）。丢掉明显超出窗口的卡片。

翻页：沿着搜索结果的下一页走，直到没有新的 `/job/{id}` 链接。用岗位 ID 在平台内去重。规范链接写成 `https://hk.jobsdb.com/job/{id}`。

从卡片收集：岗位名、公司、地点、JD 链接、是否带站内 Quick Apply。看不出申请方式时，打开岗位页再判断。

## 职业分类

注册或完善资料时，按简历和选岗范围选最接近的一项；拿不准再问一次。不要编一个与候选人无关的分类。

## Private Advertiser

没有 Quick Apply、只显示 Private Advertiser 的广告，不要走一键投递。按 [applying.md](applying.md) 看成外部申请，或直接跳过。
