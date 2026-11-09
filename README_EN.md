[简体中文](README.md) | [English](README_EN.md)

# hk-auto-apply

A [Grok Bot](https://docs.x.ai/grok-bot/skills-routines-and-automations) skill for Hong Kong job applications: finish the matching roles on [JobsDB](https://hk.jobsdb.com) and [LinkedIn](https://www.linkedin.com), then check for new ones on the schedule you choose.

**Resume + role scope → backlog apply + cross-platform dedup + tracker / research note → weekday incremental apply**

This is not an official xAI repository. There is no service to deploy, and the repo does not include anyone's resume or account.

## One message in Grok Bot

```text
Please install this GitHub skill: https://github.com/PoetCoderJun/hk-auto-apply

Read START.md and save the entire skill/hk-auto-apply directory to my skill library (SKILL.md, references, and scripts — not SKILL.md alone). Then tell me what I still need to provide.
```

Then send a resume and describe or upload the role scope.

## What you get

1. **Backlog apply**: submit matching, submittable Hong Kong roles from roughly the last 30 days, then write an analysis note and an application log.
2. **Cross-platform dedup**: when both platforms are in scope, the same company and substantially the same title are applied once.
3. **Daily new roles**: incremental checks at the time you choose; matching roles are submitted, and you still get a short update when nothing new qualifies.

## What to prepare

The bot collects files, facts, and preferences first, and only asks for whatever is still missing.

**Files**
- Resume (PDF or Word)
- Role scope: typed text or a document that can be read as prefer / consider / hard exclude / soft flag

**Facts** (skip anything already on the resume)
- Hong Kong work status or visa, expected monthly salary, and earliest start date

**Preferences**
- JobsDB, LinkedIn, or both
- Apply matching roles directly, or confirm a list first
- Run on the cloud computer, or on your own computer
- When the daily check should run (default: about 09:00 on weekdays in your timezone)

Do not send login passwords to the bot. Sign-in happens on the computer actually used for the run: take it over and log in yourself, or let the assistant drive login there. If you use your own computer, keep it on and online during the run and when the scheduled check fires.

## Repository layout

```text
START.md                         paste-ready install note for Grok Bot
skill/hk-auto-apply/
  SKILL.md                       entrypoint: workflow, constraints, what to read
  agents/openai.yaml
  references/                    intake, login, platforms, search, apply, queue, selection, dedup, reporting
  scripts/                       dedup and JD signal extraction
tests/
```

Who the candidate is, which roles to target, and what to put on application forms all come from the materials you provide after install. They are not hardcoded in the skill.

## License

[MIT](LICENSE). Not affiliated with xAI, SEEK/JobsDB, or LinkedIn.
