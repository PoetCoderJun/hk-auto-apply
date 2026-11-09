# 发现队列、deferred 与断点续投

海投会跑很久，可能被限流、登录墙，或被用户临时插入的其他任务打断。必须把发现、覆盖、投递进度落到磁盘上。中断之后只读状态续跑，不要重新当成「全新发现」再扫一遍整网。

域级节流与冷却见 [rate-limit-and-pacing.md](rate-limit-and-pacing.md)。搜岗分区见 [search-coverage.md](search-coverage.md)。

## 建议文件

放在本次运行目录里即可：

| 文件 | 用途 |
| --- | --- |
| `evidence/pacing_config.json` | 节流参数（只可放慢） |
| `evidence/request_log.jsonl` | 每次顶层请求的时间戳、域、状态码、Retry-After 是否出现 |
| `evidence/rate_limit_state.json` | 域冷却、`next_allowed_at`、guest 窗口计数 |
| `evidence/search_coverage_backfill.json` | backfill 分区游标与状态 |
| `evidence/search_coverage_incremental.json` | 每次增量任务的分区（与 backfill 分开） |
| `evidence/campaign_state.json` | backfill / incremental 完成标记（可选） |
| `evidence/pages/...` | 成功页快照或错误记录（无 PII） |
| `discovered.jsonl` | 每发现一个岗一行 |
| `deferred.jsonl` | 429/超时/JD 未读成功等，待重试（**不是**最终不投） |
| `apply_queue_remaining.json` | 尚未处理、且已具备可读 JD 的岗 |
| `apply_log.jsonl` | **仅**最终 `applied` 或硬规则 `skipped` 的证据 |
| `progress.md` | 大约每处理 10 个岗更新一次，方便中途汇报 |

`discovered.jsonl` 字段示例：`platform`、`job_id`、`title`、`company`、`url`、`found_at`、`location`、`partition_id`

`deferred.jsonl` 字段示例：

```json
{
  "ts": "2026-01-01T00:00:00Z",
  "job_id": "...",
  "platform": "linkedin",
  "url": "https://www.linkedin.com/jobs/view/...",
  "reason": "jd_fetch_429",
  "attempts": 1,
  "next_retry_at": "2026-01-01T00:05:00Z",
  "notes": "wait domain cooldown"
}
```

`apply_log.jsonl` 一行字段：

```json
{
  "ts": "2026-01-01T00:00:00Z",
  "job_id": "...",
  "title": "...",
  "company": "...",
  "url": "https://...",
  "result": "applied",
  "reason": null,
  "apply_method": "easy_apply",
  "confirmation": "页面上的成功原文或 null",
  "notes": "短备注"
}
```

- `result` 只能是 `applied` 或 `skipped`。`skipped` 只用于**已读 JD 或用户接受后**的硬不匹配、已关闭岗等，见 [applying.md](applying.md) 与 [selection.md](selection.md)。
- **不要**把 `jd_fetch_429`、`search_truncated`、重试耗尽等资源/覆盖类原因写进 `apply_log` 的 `skipped`；岗位级留在 `deferred.jsonl`，分区级留在 `search_coverage_backfill.json` 或 `search_coverage_incremental.json`。
- `reason` 用稳定的英文蛇形词。跟踪表备注再写成中文。
- `job_id` 已在 `apply_log.jsonl` 里 `applied` 的，不要再投。

统计汇报时区分：**唯一岗位数**（按 `job_id`）、**retry 事件次数**（`deferred`/`request_log` 可多于岗位数）、**apply_log 行数**（终态）。

每处理完一个可投递岗：先追加 `apply_log.jsonl`，再从剩余队列删掉并更新 `count`。**立刻**写盘。

从队列移除前，若岗曾被 deferred，确认已写入 `deferred.jsonl` 或已转入终态，避免 silent drop。

## 可投递（eligible）与首轮完成

**可投递岗**同时满足：

- 已在 `discovered.jsonl`（或当次增量等价发现记录）
- JD 已当场读过且正文完整（非 `deferred` 的 `jd_fetch_*`）
- 通过选岗规则，且未在 `apply_log` 有终态
- 不在硬去重重复集合内

这类岗应在 `apply_queue_remaining.json` 中排队；处理完写 `apply_log`，再从队列移除。

**首轮（backfill）完成**（见 [search-coverage.md](search-coverage.md)）= backfill 计划分区全部 `complete` **且** 上述可投递岗全部进入 `apply_log` 终态。仅队列空 **不能** 证明完成。

`deferred.jsonl` 中的岗在恢复为可投递之前，不参与「队列已清空」的完成判定。

## 批次与汇报

首轮目标是在**计划内搜索范围**里，先完成 backfill 分区覆盖，再把所有可投递岗处理至终态；不要在大约 20 份时自行停下。搜索分区仍有 `truncated`/`deferred` 时，队列可以为空，但 coverage **不算** done，首轮 **不算** complete。

大约每处理 50 个岗可做检查点汇报（已处理 / 成功 / 跳过 / deferred / 剩余 / 覆盖 summary）。这是汇报节奏，不是战役结束。

用户叫停、登录墙、拿不到验证码、或域冷却未到点时停，并报告当前 URL、剩余队列、`next_retry_at`、以及 [search-coverage.md](search-coverage.md) 的 summary。冷却期间**不要轮询**；用定时任务在 `next_retry_at` 唤醒，不支持则告知用户暂停到何时。

## 不要预先写入跟踪表的东西

不要把整个剩余队列预先建成「待投递」。不要把 deferred 岗预先标成「不投」。只在终态决定后写跟踪表。见 [tracker-and-report.md](tracker-and-report.md)。
