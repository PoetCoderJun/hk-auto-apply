[简体中文](README.md) | [English](README_EN.md)

# hk-auto-apply

给 [Grok Bot](https://docs.x.ai/grok-bot/skills-routines-and-automations) 用的香港求职自动投递技能：在 [JobsDB](https://hk.jobsdb.com) 和 [LinkedIn](https://www.linkedin.com) 上，把符合你要求的岗位投完，再按约定时间检查新岗。

**简历 + 岗位范围 → 存量海投 + 跨平台去重 + 投递记录 / 分析报告 → 每个工作日增量投递**

这不是 xAI 官方仓库。这里没有需要单独部署的服务，也不包含任何人的简历或账号。

## 和 Grok Bot 说一句话就行

```text
请安装这个 GitHub 技能：https://github.com/PoetCoderJun/hk-auto-apply

请读取 START.md，并把仓库里的 skill/hk-auto-apply 完整保存到我的技能库（包括 SKILL.md、references 和 scripts，不要只复制 SKILL.md）。保存后告诉我还需要提供什么。
```

然后交一份简历，再说清或上传岗位范围。

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
- 日常增量检查几点跑（默认工作日早上大约 9:00，可改）

不要把登录密码发给 Bot。登录发生在实际使用的那台电脑上：你可以自行接管电脑登录，也可以让助手在这台电脑上走登录流程。选自己的电脑时，使用期间和定时任务触发时都要开机在线。

## 仓库结构

```text
START.md                         粘贴给 Grok Bot 的安装说明
skill/hk-auto-apply/
  SKILL.md                       入口：流程、硬性约束、该读哪份参考
  agents/openai.yaml
  references/                    收集资料、登录、平台、选岗、去重、报表
  scripts/                       去重和 JD 信号提取
tests/
```

候选人是谁、选哪些岗、薪资和签证填什么，都以安装后你交来的材料为准，不会写死在技能里。

## 许可

[MIT](LICENSE)。与 xAI、SEEK/JobsDB、LinkedIn 无关联。
