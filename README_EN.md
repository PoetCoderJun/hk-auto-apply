[简体中文](README.md) | [English](README_EN.md)

# hk-auto-apply

A Hong Kong job-application skill for any Personal Agent or local agent that supports Browser Use / Computer Use: finish the matching roles on [JobsDB](https://hk.jobsdb.com) and [LinkedIn](https://www.linkedin.com), then check for new ones on the schedule you choose.

**Resume + role scope → backlog apply + cross-platform dedup + tracker / research note → weekday incremental apply**

This is not an official xAI repository. There is no service to deploy, and the repo does not include anyone's resume or account.

## Install and usage

This skill can run on any Personal Agent that supports Browser Use / Computer Use, or on a local agent with the same kind of browser control. Searching, signing in, and applying all depend on that capability.

A Personal Agent such as [Grok Bot](https://docs.x.ai/grok-bot/skills-routines-and-automations) or OpenAI Dots is the smoother setup: a cloud computer can stay online, which helps with backlog apply, scheduled checks for new roles, interview reminders, and progress tracking. A local agent works too; if the run uses your own computer, keep it on and online during the run and when the scheduled check fires.

Paste this into the assistant:

```text
Please install this GitHub skill: https://github.com/PoetCoderJun/hk-auto-apply

Read START.md and save the entire skill/hk-auto-apply directory to my skill library (SKILL.md, references, and scripts — not SKILL.md alone). Then tell me what I still need to provide.
```

Then send a resume and describe or upload the role scope. The assistant collects files, facts, and preferences first, and only asks for whatever is still missing.

Do not send login passwords to the assistant. Sign-in happens on the computer actually used for the run: take it over and log in yourself, or let the assistant drive login there.

## Inputs

**Files**
- Resume (PDF or Word)
- Role scope: typed text or a document that can be read as prefer / consider / hard exclude / soft flag

**Facts** (skip anything already on the resume)
- Hong Kong work status or visa, expected monthly salary, and earliest start date

**Preferences**
- JobsDB, LinkedIn, or both
- Apply matching roles directly, or confirm a list first
- When a role has no Quick Apply / Easy Apply and opens the company's own page: default spray mode (海王模式)—fill it if it is simple, skip if it is complex; or leave-no-company-behind mode, which tries every employer page (slower and more error-prone)
- Run on the cloud computer, or on your own computer
- Keep the tracker as local Excel, Google Sheets, Feishu / Lark, Notion, or another table you name (default: a local Excel file)
- When the daily check should run (default: about 09:00 on weekdays in your timezone)

## Outputs

- An application log with a platform column
- An analysis note covering search coverage, funnel numbers, role-family judgments, and common skip reasons
- A short update after each incremental check, including when nothing new qualifies

The application log and research note do not have to live in Notion. You can keep or export them as a local Excel workbook, a Google Sheet, a Feishu / Lark sheet, or any other table you name.

## Actions

1. **Backlog apply**: submit matching, submittable Hong Kong roles from roughly the last 30 days.
2. **Cross-platform dedup**: when both platforms are in scope, the same company and substantially the same title are applied once.
3. **Fill applications**: complete on-site Quick Apply / Easy Apply; when a role opens the company's own page, follow spray mode or leave-no-company-behind mode as you chose.
4. **Daily new roles**: incremental checks at the time you choose; matching roles are submitted and the tracker is updated.

## Repository layout

```text
START.md                         paste-ready install note
skill/hk-auto-apply/
  SKILL.md                       entrypoint: workflow, constraints, what to read
  agents/openai.yaml
  references/                    intake, login, platforms, search, apply, queue, selection, dedup, reporting
  scripts/                       dedup and JD signal extraction
```

Who the candidate is, which roles to target, and what to put on application forms all come from the materials you provide after install. They are not hardcoded in the skill.

## License

[MIT](LICENSE). Not affiliated with xAI, SEEK/JobsDB, or LinkedIn.
