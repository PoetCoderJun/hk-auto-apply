# 搜岗覆盖状态（分区、游标、续跑）

目标是在**计划内的关键词与时间窗**里尽可能完整地收集岗位卡片，并如实标明 `complete` / `truncated` / `deferred`。不声称「整个 LinkedIn 香港站已搜全」。

## 分区键

每个搜岗分区至少包括：

- `platform`：`linkedin_guest` | `linkedin_signed_in` | `jobsdb`
- `keyword` 或 JobsDB 路径 slug
- `time_window`：例如 LinkedIn `f_TPR=r2592000`（近 30 天）、增量时的 `since_last_run`
- `partition_id`：稳定字符串，例如 `linkedin_guest|r2592000|assistant+relationship+manager`

**`backfill`（首轮存量）** 与 **`incremental`（每日新岗）** 必须分开落盘、分开汇报，不要混写或互相覆盖：

- `evidence/search_coverage_backfill.json`：`campaign: "backfill"`，计划内关键词 + 近约 30 天窗（或用户指定的存量窗）
- `evidence/search_coverage_incremental.json`：`campaign: "incremental"`，每次定时任务自己的分区与 `since_last_run` / 重叠窗

可选总览 `evidence/campaign_state.json`：

```json
{
  "backfill": {
    "status": "in_progress",
    "search_complete": false,
    "apply_complete": false,
    "completed_at": null
  },
  "incremental": {
    "status": "idle",
    "last_run_at": null,
    "last_run_search_complete": null,
    "last_run_apply_complete": null
  }
}
```

`status` 取值：`in_progress` | `paused`（用户叫停或域冷却，已写入 `next_retry_at`）| `complete`。

## 状态文件

建议 `evidence/search_coverage_backfill.json`（增量文件结构相同，仅 `campaign` 为 `incremental`）：

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

## 首轮（backfill）什么叫「做完」

向用户说「首轮存量结束」、写终版分析报告、或建立**仅针对增量的**定时任务之前，**同时**满足下面两条。缺任意一条都只能报「进行中 / 暂停」，不能报完成。

### A. 计划内搜岗覆盖（backfill 文件）

对 `search_coverage_backfill.json` 里**本轮计划中的每个** `partition_id`：

- 状态必须是 `complete`（已验证分页自然终止）。
- 不得仍有 `planned`、`in_progress`、`truncated`，或处于等待重试的 `deferred`（搜岗分区未 `complete` 即覆盖未完成）。
- 用户书面同意放弃某个词/分区除外——须在报告里单列「用户接受未覆盖分区」及原因，且不得把该分区标成 `complete`。

域冷却或 `next_retry_at` 未到、分区仍未 `complete` 时：标 `campaign_state.backfill.status = paused`，说明预计续跑时间，**不要**称首轮完成。

### B. 可投递队列（非 deferred 且符合条件）

在 backfill 已发现、且 **JD 已可读**、已通过 [selection.md](selection.md) 标题/JD 规则、未与跟踪表/日志重复的所有岗位中：

- `apply_queue_remaining.json` 的 `count` 必须为 **0**。
- 每个这样的岗必须在 `apply_log.jsonl` 中有终态一行：`applied` 或硬规则 `skipped`。
- `deferred.jsonl` 中凡属 backfill 发现、仍可能变为可投的岗（如 `jd_fetch_*`、`search_truncated` 后尚未重读 JD），在重试完成并进入终态之前，**不得**视为首轮 apply 完成。

`discovered` 中有卡片但 JD 从未读成功、且仍在 deferred 等待重试 → **首轮未完成**，即使 `apply_queue_remaining` 暂时为 0。

### 与增量的关系

- backfill 的 `complete` **不**被「增量定时任务已创建」替代；可以先在 `paused` 状态下与用户约好增量时间，但报告须写清 backfill 仍缺覆盖或 deferred。
- 每次 incremental 只更新 `search_coverage_incremental.json` 与当次 `campaign_state.incremental.*`；**不要**用增量队列空来证明 backfill 搜索已完成。
- 分析报告分开两节：**Backfill 状态**（A+B 是否满足）与 **Incremental 最近一次**（仅当次计划分区 + 当次队列）。

## 增量（incremental）单次什么叫「做完」

一次定时增量 run 结束（或暂停）时，分别记录：

1. **当次搜索**：本次 incremental 计划内分区是否全部 `complete`，否则标 `truncated`/`deferred` 并写入 `last_run_search_complete: false`。
2. **当次投递**：当次新进入、JD 可读且符合条件的队列是否已处理至 `apply_log` 终态；`deferred` 仅影响当次投递完成标记，不 retroactively 关闭 backfill。

不要求一次 incremental 去补齐历史 backfill 的 truncated 分区；补缺口应用 **backfill 续跑**（仍写 `search_coverage_backfill.json`），与 incremental 分区表分开。
