# 搜岗覆盖状态（分区、游标、续跑）

目标是在**计划内的关键词与时间窗**里尽可能完整地收集岗位卡片，并如实标明 `complete` / `truncated` / `deferred`。不声称「整个 LinkedIn 香港站已搜全」。

## 分区键

每个搜岗分区至少包括：

- `platform`：`linkedin_guest` | `linkedin_signed_in` | `jobsdb`
- `keyword` 或 JobsDB 路径 slug
- `time_window`：例如 LinkedIn `f_TPR=r2592000`（近 30 天）、增量时的 `since_last_run`
- `partition_id`：稳定字符串，例如 `linkedin_guest|r2592000|assistant+relationship+manager`

同一 campaign 里 **首轮存量** 与 **每日新岗** 用不同的 `campaign` 字段区分（`backfill` vs `incremental`），不要混在一个分区表里覆盖写。

## 状态文件

建议 `evidence/search_coverage.json`：

```json
{
  "campaign": "backfill",
  "partitions": [
    {
      "partition_id": "linkedin_guest|r2592000|product+manager",
      "platform": "linkedin_guest",
      "keyword": "product manager",
      "time_window": "r2592000",
      "status": "truncated",
      "last_success_start": 20,
      "next_cursor": 20,
      "pages_fetched": 3,
      "cards_collected": 27,
      "next_retry_at": "2026-11-09T10:30:00Z",
      "last_error": {"code": 429, "at": "...", "retry_after_sec": null}
    }
  ],
  "summary": {
    "complete": 12,
    "truncated": 18,
    "deferred": 6,
    "in_progress": 0
  }
}
```

`status` 取值：

| 状态 | 含义 |
| --- | --- |
| `planned` | 尚未开始 |
| `in_progress` | 正在翻页，游标有效 |
| `complete` | 已验证到自然终止（如 guest 返回少于 10 张卡的最后一页） |
| `truncated` | 因 429/挑战/用户叫停，页链未走完 |
| `deferred` | 等待 `next_retry_at` 后从 `next_cursor` 续跑 |

**只有**验证过分页终止才标 `complete`。队列空、或某词只翻了 2 页就 429，都不能标 complete。

## 游标与续跑规则

- `next_cursor` 是**下一次要请求的 `start` 偏移**（或 JobsDB 的下一页 URL/页码）。失败时保存在**失败那一页**，不要 blindly 用 `last_success_start + 10` 跳过未验证的页。
- 若 `last_success_start` 为 0 且第一页就 429，`next_cursor` 必须是 `0`，不是 `10`。
- 续跑前读 `discovered.jsonl` 与分区里已记录的 `job_id`，合并去重后再请求。
- 为追上「最新列表」，增量可以与旧 backfill **时间窗重叠**，允许重复页；用岗位 ID 去重，不要为了省请求而假装 30 天窗可以过滤到某一天。

恢复**很久以前**未完成的 truncated 分区时，必须用该分区原始的 `time_window` 边界续搜，不要只搜「自上次运行以来」而把旧缺口永远丢掉。

每成功拉取一页：追加 `evidence/pages/{partition_id}/{start}.json` 或等价快照（卡片列表、HTTP 状态、时间戳）。失败页写 `evidence/pages/.../error.json`。

## 与队列、投递的关系

- 覆盖未完成 ≠ 投递队列空。报告里分开写：**计划内搜索**的 complete/truncated/deferred 计数，以及 **apply 队列**剩余数。
- 发现卡片先进 `discovered.jsonl`；JD 未读成功、429、超时的岗进 `deferred.jsonl`（见 [queue.md](queue.md)），**不要**写入 `apply_log.jsonl` 的 `skipped`。
- 分析报告必须列出：各平台各词的 `complete` / `truncated` / `deferred` 数量及原因（429、挑战页、超时、用户暂停等），并说明范围是「本次计划关键词与时间窗」，不是全站。
