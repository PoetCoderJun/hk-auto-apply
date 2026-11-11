# 跨平台去重

两个平台都要全量海投，但不要重复投同一个机会。先在平台内按岗位 ID 去重，再和跟踪表比对。

用脚本做机械比对，不要只靠肉眼扫标题：

```bash
python3 "$SKILL_DIR/scripts/dedup.py" --jobs jobs.json --tracker tracker.json
```

`jobs.json` 和 `tracker.json` 都是对象数组，字段至少包括 `company`、`title`、`url`、`platform`。跟踪表行还应有 `status`。脚本会给每条待处理岗位标上是否重复、命中了哪条记录，以及原因。

判定规则：

- 同一个 JD 链接（含同一岗位 ID 的不同查询参数）算重复。
- 同一家公司加实质相同的岗位名算重复。忽略大小写和标点；`Assistant RM`、`Assistant Relationship Manager` 与 `ARM` 算同一岗。公司名里的 `Limited` / `Ltd` / `有限公司` 等后缀忽略。
- 若跟踪表里已是「已投递」，不要在另一个平台再投，记成「不投」并备注「与 [JobsDB/LinkedIn] 已投递岗位重复」。
- 若表里已是「不投」且原因仍适用，也不要再投，备注「与 [JobsDB/LinkedIn] 不投记录重复」。
- 同一公司的不同岗位（例如 KYC 与 RM）不算重复，要独立按选岗规则判。

脚本给出 `duplicate: true` 后，仍要看跟踪表状态和原备注是否仍然适用，再写「不投」备注。
