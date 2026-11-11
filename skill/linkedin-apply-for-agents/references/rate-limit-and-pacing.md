# 域级节流、429 与证据日志

LinkedIn guest 搜岗、已登录搜岗、岗位页 JD 读取，以及 JobsDB 搜索翻页，都属于**对同一招聘域发起的顶层导航或顶层 HTTP 请求**。浏览器会自动拉取 CSS、图片、字体等子资源；助手**不能**假装能单独调度那些子资源，只能控制：何时发起下一次顶层搜岗/翻页/JD 打开/关键 UI 点击。

实操默认见下文「运行级默认参数」。这些都是**偏保守的运行默认值**，不是 LinkedIn/JobsDB 官方限额，也不保证永不 429。只允许**放慢**，收到 429 或进入冷却后**禁止**再加快。

跨所有 Agent 会话、脚本和人工接管，对同一域遵守：

- **同一时间只进行一个进行中的顶层请求**（搜岗页、guest API 页、岗位 JD 页、JobsDB 搜索结果页）。不要并行刷多个关键词，也不要开第二个 Agent 会话抢同一账号搜岗。
- 两次顶层请求之间留足间隔；换关键词前额外留更长间隔（见默认参数）。
- UI 点击前先等页面稳定（列表渲染完、无加载遮罩），看到成功确认再记结果；两次关键点击之间至少留出文档里的示意等待（通常 2–4 秒），不要连点。

## 运行级默认参数（可写进 `evidence/pacing_config.json`）

以下为起始默认值；可在配置里**只增大**间隔或**减小**每 10 分钟 guest 上限，不要减小间隔来「赶进度」。

| 项 | 默认 | 说明 |
| --- | --- | --- |
| `min_top_level_gap_sec` | 10–20（建议先用 15） | 任意两次顶层请求之间的最短间隔（秒） |
| `guest_rolling_window_sec` | 600 | 滚动窗口长度（10 分钟） |
| `guest_max_requests_per_window` | 20 | 窗口内 guest 顶层请求上限 |
| `min_gap_between_keywords_sec` | 60 | 结束一个词、开始下一个词前至少等待 |
| `ui_action_min_gap_sec` | 2–4（建议 3） | 关键 UI 操作之间的示意最短间隔 |
| `backoff_steps_sec` | 30, 60, 120 | 单请求 429 后的指数回退阶梯 |
| `backoff_jitter_max_sec` | 5 | 每步加 0–jitter 的随机偏移 |
| `max_retries_per_request` | 2 | 同一顶层请求最多重试次数，之后标记该分区 deferred |
| `domain_cooldown_sec` | 1800 | 超过重试上限或触发断路后，全域冷却（30 分钟） |
| `consecutive_429_for_circuit` | 3 | 连续 3 次 429（跨岗位或跨查询）立即进入全域冷却 |

配置里应记录 `updated_at` 和变更原因（例如「实战中 guest 仍 429，间隔调到 20s」）。

## 证据日志（无凭证、无 PII）

在本次运行目录下维护：

- `evidence/pacing_config.json`：当前节流参数（见上表字段）。
- `evidence/request_log.jsonl`：每行一次顶层请求，例如  
  `{"ts":"...","domain":"www.linkedin.com","kind":"guest_search","keyword":"...","start":20,"status":429,"retry_after_sec":null,"note":"no Retry-After header"}`  
  - 有 `Retry-After`（秒或 HTTP-date）时写入解析后的 `retry_after_sec` 或 `retry_after_at`。  
  - **没有**该头时写 `null`，并在 `note` 里说明「未提供 Retry-After」，**不要**编造官方等待时间。
- `evidence/rate_limit_state.json`：域级 `next_allowed_at`、`domain_cooldown_until`、`consecutive_429_count`、各分区 `next_retry_at` 等（可用 [scripts/pacing_gate.py](../scripts/pacing_gate.py) 读写）。

请求前：若 `now < next_allowed_at`，**不要轮询**；把 `next_retry_at` 写入状态，用宿主支持的定时任务/ schedule 在到点后再跑；不支持定时则向用户报告「已暂停，预计 HH:MM 再续」。

## 收到 HTTP 429

1. **立刻**落盘：该次请求日志、触发 429 的分区状态、全局 `consecutive_429_count`。
2. 若响应带 `Retry-After`：尊重其秒数或日期，作为该请求/分区的 `next_retry_at` 下限。
3. 若无 `Retry-After`：不声称官方等待时长，用运行级 capped 回退并加小抖动：第 1 次 429 后约 **30s**、第 2 次约 **60s**（第 3 次触及 429 时用 **120s** 阶梯计算下一次，但通常已触发 deferred/冷却）。同一 `keywords+start`（或同一 JD URL）**最多 2 次重试**（含初次失败，至多 3 次 429），之后标 deferred 或进入域冷却。
4. 仍失败：该搜索分区标为 `deferred` 或 `truncated`，写入 `next_retry_at`；若已耗尽单请求重试或 `consecutive_429 >= 3`，设置 `domain_cooldown_until = now + 30min`，停止该域一切顶层请求直到冷却结束。
5. 冷却期间**不要**用缩短 sleep、并发、换 IP、换无头模式、换账号等方式绕过；向用户说明暂停原因与预计恢复时间。

## 挑战页、登录墙、反爬

返回 Cloudflare/验证墙、要求登录、或明显「非正常搜索结果」时：**停止该路由**，记录状态，请用户接管或改用已在用户授权下的**已登录**浏览器搜索（见 [linkedin-search.md](linkedin-search.md)）。已登录搜索是正当主路径或 guest 不可用时的回退，**不是**为了绕过 429 控制而开的侧门。

简单验证码可在正常浏览器里尝试一次；确实过不去再交给用户，**不要**使用第三方打码/绕过服务。

不要把「全域冷却倒计时」和「等页面加载 3 秒」混为一谈：前者必须 schedule 唤醒，后者只是单次 UI 等待。

## JobsDB

JobsDB 同样遵守单域单飞、顶层间隔和 429/超时记录。JobsDB 较少 429，但超时或空结果页要按 [search-coverage.md](search-coverage.md) 标 `deferred`，不要直接记成不投。

## 辅助脚本

确定性节流与 429 状态机可用：

```bash
python3 SKILL_DIR/scripts/pacing_gate.py self-check
python3 SKILL_DIR/scripts/pacing_gate.py plan-next --state evidence/rate_limit_state.json --domain www.linkedin.com
```

搜岗分区与翻页游标见 [search-coverage.md](search-coverage.md)。队列与 deferred 见 [queue.md](queue.md)。
