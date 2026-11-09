---
name: hk-auto-apply
description: >-
  Starts Hong Kong JobsDB and/or LinkedIn auto-apply after the user provides
  a resume and a job scope. Use when installing this GitHub skill, or when the
  user mentions 香港求职, 海投, 自动投简历, JobsDB, LinkedIn 投递, or weekday
  checks for new Hong Kong postings. Collects files, facts, and preferences
  first and chases any gaps. Runs on the cloud computer or the user's own
  computer and never asks for login passwords. Do not use for job sites the
  user did not name.
license: MIT
metadata:
  author: PoetCoderJun
  homepage: https://github.com/PoetCoderJun/hk-auto-apply
  short-description: Hong Kong JobsDB and LinkedIn auto-apply
---

# hk-auto-apply

把用户交来的简历和岗位范围，在他们点名的香港平台（JobsDB 和/或 LinkedIn）上做成两件事：先把近约 30 天里符合规则、能投的存量岗位投完，并写出带「平台」列的投递记录和分析报告；再按约定时间做增量检查。

候选人是谁、选哪些岗、申请表填什么，都以当前这位用户交来的材料为准。不要套用其他候选人的简历、薪资或筛选标准，不要编造牌照、语言、地址、身份证或额外年限。

把 `SKILL_DIR` 解析为包含本 `SKILL.md` 的目录。只读取当前步骤需要的 reference，脚本从 `SKILL_DIR/scripts` 运行。

## 按需阅读

- 安装后收集材料，或用户交来的不齐全：读 [references/intake.md](references/intake.md)
- 选择云电脑还是用户自己的电脑，以及登录：读 [references/runtime.md](references/runtime.md)
- 在某个平台上搜岗或投递：读 [references/platforms.md](references/platforms.md)
- 把岗位范围编成可执行规则，或阅读 JD：读 [references/selection.md](references/selection.md)
- 两个平台都投、需要去重：读 [references/dedup.md](references/dedup.md)
- 建跟踪表、写分析报告、设每日增量任务：读 [references/tracker-and-report.md](references/tracker-and-report.md)

## 流程

1. 若用户说「请安装这个 GitHub 链接」并指向本仓库：把整个 `skill/hk-auto-apply` 目录保存到技能库，包括 `references/` 和 `scripts/`，不要只复制 `SKILL.md`。保存后立刻按 intake 把「文件 / 信息 / 偏好」清单发给用户。
2. 只做用户点名的平台。说 JobsDB 和 LinkedIn、两个都投，或在 JobsDB 同等逻辑上加入 LinkedIn，就两边都全量海投并去重。只点其中一个时，不要自行扩到另一个，也不要扩到没点名的求职网站。
3. 问清这次跑在云电脑还是用户自己的电脑，然后在那台电脑上完成登录。不要向用户要密码。
4. 打开或创建带「平台」列的跟踪表。双平台时，投之前先做去重。
5. 第一次使用：把近约 30 天内符合规则且能投的岗都投完，不要在大约 20 份时自行停下。有进度和卡点都及时告诉用户。
6. 首轮结束后写完分析报告，并按用户确认的时间建立增量定时任务。
7. 定时任务只处理上次之后新出现、或表里还没有的岗位；用同一套规则、去重和跟踪表；没有新的可投岗位时也发一条短消息。

## 硬性约束

- 必须项未齐之前，不要开始搜岗或投递。
- 不要向用户索要 JobsDB 或 LinkedIn 的登录密码。如果他们主动发了密码，不要写回聊天，也不要写进通用技能文本。
- 只有看到成功确认，才把该岗记成已投递。
- 外部公司申请页简单就填，复杂就跳过并记下原因。
- 可选封面信就跳过；必填时只根据简历写一小段事实。必填字段不知道就跳过该岗，不要填假。
- 不要删除跟踪表里的探测行或重复行，除非用户明确要求。

## 交付

按平台拆开汇报：唯一卡片数、标题匹配数、成功投出数、按原因归类的跳过数、跨平台重复数、跟踪表链接、调研文档链接，以及定时任务会在几点跑。若跑在用户自己的电脑上，同时提醒他们到点需要开机。
