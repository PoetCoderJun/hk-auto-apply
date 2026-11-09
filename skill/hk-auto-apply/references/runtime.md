# 运行环境与登录

本技能可以跑在任何支持 Browser Use 或 Computer Use 的 Personal Agent 上，也可以跑在具备同等浏览器操作能力的本地 Agent 上。搜岗、登录和投递都依赖这种浏览器操作；没有它就无法自动投递。

更建议使用带云电脑的 Personal Agent，例如 Grok Bot 或 OpenAI Dots：云电脑比较容易保持在线，方便完成存量海投、按点增量投递，以及之后的面试提醒和进度跟踪。本地 Agent 也可以用，但选用户自己的电脑时，使用期间和定时任务触发时都要开机在线。

这次投递可以跑在 bot 的云电脑上，也可以跑在用户自己的电脑上。开投前问清用哪一台。如果站点拦数据中心 IP，云电脑可能打不开或频繁被验证，这时改到用户自己的电脑，或让浏览走用户的电脑网络。

若用户选择自己的电脑：使用期间那台电脑要开机并保持在线；日常定时任务触发时也要开机在线，否则这次增量检查跑不了。

## 登录原则

登录发生在实际使用的那台电脑上。不要向用户索要 LinkedIn 或 JobsDB 的登录密码。按用户的选择用下面两种方式之一：

1. 用户自行接管这台电脑，自己登录 LinkedIn 和/或 JobsDB。登完再把控制交回，助手接着投递。
2. 用户让助手在这台电脑的浏览器里走登录流程。JobsDB 验证码如果发到 bot 信箱或已连接邮箱，助手自己取。出现手机 App 确认、验证码发到用户自己的设备、passkey 或必须本人操作的步骤时，把屏幕交给用户完成，不要猜验证码。

如果用户主动在聊天里发了密码，也不要写回聊天或写进通用技能文本；优先仍请他们在这台电脑上自己输入，或自行接管登录。

登录墙、验证码拿不到，或需要用户本人接管电脑时，马上告诉他们并等，不要假装已经投出。

## 限流暂停与定时续跑

LinkedIn/JobsDB 域冷却或分区 `next_retry_at` 未到之前，不要 busy-wait 或缩短间隔重试。把 `evidence/rate_limit_state.json` 与 `search_coverage_backfill.json` / `search_coverage_incremental.json`（及其中各分区的 `next_retry_at`）写入进度汇报；用宿主支持的 **schedule / 定时任务** 在到点后自动续跑；若当前环境不支持，明确告诉用户「已暂停至 HH:MM（时区）」。

续跑时先读 [search-coverage.md](search-coverage.md) 与 [queue.md](queue.md)：backfill 缺口写 `search_coverage_backfill.json`，增量写 `search_coverage_incremental.json`；从失败游标和 `deferred.jsonl` 继续。在 backfill 未达完成条件前，不要用「增量已跑过」抵扣首轮覆盖。同一账号、同一时刻仍只保留一个进行中的搜岗/JD 顶层会话。
