# 发现队列与断点续投

海投会跑很久，可能被限流、登录墙，或被用户临时插入的其他任务打断。必须把发现和投递进度落到磁盘上。中断之后只读队列续跑，不要重新当成「全新发现」再扫一遍整网。

## 建议文件

放在本次运行目录里即可：

- `discovered.jsonl`：每发现一个岗一行，字段包括 `platform`、`job_id`、`title`、`company`、`url`、`found_at`、`location`
- `apply_queue_remaining.json`：`{"count": N, "jobs": [尚未处理的岗]}`
- `apply_log.jsonl`：每处理完一个岗追加一行，作为唯一的已处理证据
- `progress.md`：大约每处理 10 个岗更新一次，方便中途汇报

`apply_log.jsonl` 一行的字段：

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

- `result` 只能是 `applied` 或 `skipped`。只有页面出现成功确认之后才能写成 `applied`，见 [applying.md](applying.md)。
- `apply_method` 常用 `easy_apply` / `linkedin_easy_apply` / `quick_apply` / `external`；跳过且未开申请页时用 `null`。
- `reason` 用稳定的英文蛇形词，例如 `external_ats_complex`、`5plus_years_hard_requirement`、`cantonese_hard_requirement`、`required_relevant_experience_not_met`、`unknown_required_field`。跟踪表备注再写成中文。
- `job_id` 已经出现在 `apply_log.jsonl` 里的，不要再投。

每处理完一个岗：先追加一行到 `apply_log.jsonl`，再从剩余队列里删掉它并更新 `count`。必须马上写入磁盘，不要等一整批结束。

## 批次与汇报

首轮目标仍是把符合规则、能投的岗投完，不要在大约 20 份时自行停下。

为了及时告诉用户进度，可以大约每处理 50 个岗做一次检查点汇报（已处理 / 成功 / 跳过 / 剩余）。这是汇报节奏，不是战役结束。汇报之后马上从队列头部继续。

用户叫停、遇到登录墙、拿不到验证码，或限流过不去时才停，并报告当前页面地址和已经落盘的剩余数量。

## 不要预先写入跟踪表的东西

不要把整个剩余队列预先建成「待投递」。只在决定不投、真正投出、或现场跳过时写跟踪表。见 [tracker-and-report.md](tracker-and-report.md)。
