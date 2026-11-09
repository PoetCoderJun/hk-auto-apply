[简体中文](README.md) | [English](README_EN.md)

# hk-auto-apply

给支持 Browser Use / Computer Use 的 Personal Agent 或本地 Agent 用的香港求职自动投递技能：在 [JobsDB](https://hk.jobsdb.com) 和 [LinkedIn](https://www.linkedin.com) 上，把符合你要求的岗位投完，再按约定时间检查新岗。

**简历 + 岗位范围 → 存量海投 + 跨平台去重 + 投递记录 / 分析报告 → 每个工作日增量投递**

这不是 xAI 官方仓库。这里没有需要单独部署的服务，也不包含任何人的简历或账号。

## 运行环境

本技能可以跑在任何支持 Browser Use / Computer Use 的 Personal Agent，或具备同等浏览器操作能力的本地 Agent 上。搜岗、登录和投递都依赖这种浏览器操作。

更建议使用 Personal Agent，例如 [Grok Bot](https://docs.x.ai/grok-bot/skills-routines-and-automations) 或 OpenAI Dots。这类助手比较容易接上云电脑、保持在线，适合自动投递、按点检查新岗，以及后续的面试提醒和进度跟踪。本地 Agent 也可以用；如果投递跑在你自己的电脑上，使用期间和定时任务触发时都要开机在线。

投递记录和分析报告不必写成 Notion 文档。可以导出或维护为本地 Excel、Google 表格、飞书表格，或你指定的其他表格。

## 和 Grok Bot 说一句话就行

```text
请安装这个 GitHub 技能：https://github.com/PoetCoderJun/hk-auto-apply

请读取 START.md，并把仓库里的 skill/hk-auto-apply 完整保存到我的技能库（包括 SKILL.md、references 和 scripts，不要只复制 SKILL.md）。保存后告诉我还需要提供什么。
```

然后交一份简历，再说清或上传岗位范围。其他支持安装 GitHub 技能、并且能做 Browser Use / Computer Use 的助手，也可以用同一套文件。

## 你会得到什么

1. **存量海投**：近约 30 天里符合要求、能投的香港岗位投完，并写出分析报告和投递记录。
2. **跨平台去重**：两个平台都投时，同一公司、实质相同的岗位只投一次。
3. **每日新岗**：按你约定的时间做增量检查；有合适的就投，没有也会回一句。

## 开投前请准备

Bot 会按「文件 / 信息 / 偏好」收集材料，缺什么只追问缺的那几项。

**文件**
- 简历（PDF 或 Word）
- 岗位范围：打字或上传选岗说明，要能读出优先、可考虑、硬性排除、软性提示

**信息**（简历里有的不用再给）
- 香港工作身份或签证、期望月薪、预计可入职时间

**偏好**
- 做 JobsDB、LinkedIn，还是两个都投
- 符合要求是直接投，还是先确认名单
- 跑在云电脑，还是你自己的电脑
- 跟踪表放在本地 Excel、Google 表格、飞书、Notion，还是你指定的其他表（没说就先给本地 Excel）
- 日常增量检查几点跑（默认工作日早上大约 9:00，可改）

不要把登录密码发给 Bot。登录发生在实际使用的那台电脑上：你可以自行接管电脑登录，也可以让助手在这台电脑上走登录流程。选自己的电脑时，使用期间和定时任务触发时都要开机在线。

## 仓库结构

```text
START.md                         粘贴给助手的安装说明
skill/hk-auto-apply/
  SKILL.md                       入口：流程、硬性约束、该读哪份参考
  agents/openai.yaml
  references/                    收集资料、登录、平台、搜索、填表、队列、选岗、去重、报表
  scripts/                       去重和 JD 信号提取
tests/
```

候选人是谁、选哪些岗、薪资和签证填什么，都以安装后你交来的材料为准，不会写死在技能里。

## 许可

[MIT](LICENSE)。与 xAI、SEEK/JobsDB、LinkedIn 无关联。
