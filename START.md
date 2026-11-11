# Install linkedin-apply-for-agents

You are installing a skill from https://github.com/PoetCoderJun/linkedin-apply-for-agents

The previous repository name `hk-auto-apply` and URL https://github.com/PoetCoderJun/hk-auto-apply still redirect here. Treat `hk-auto-apply` as an alias of this skill. Always save the `skill/linkedin-apply-for-agents` directory, not a compatibility stub.

This is a LinkedIn auto apply skill for agents that support Browser Use / Computer Use. It works best on Grok Bot or OpenAI Dots: they have a cloud computer that can stay on around the clock, can automatically track application-related email, and can trigger the daily check and send updates on their own. It also runs on ordinary agents with Browser Use / Computer Use, such as Codex, Claude, Cursor, and Kimi.

The target location is required at the start. Always apply on LinkedIn using that location's geoId. If the location is Hong Kong, also apply on JobsDB automatically. Never ask the user to choose platforms.

1. Read `skill/linkedin-apply-for-agents/SKILL.md`.
2. Save the entire `skill/linkedin-apply-for-agents` directory into the skill library, including `references/` and `scripts/`. Do not save only the `SKILL.md` text.
3. Keep the name and description from that `SKILL.md` unchanged.
4. After it is saved, follow `skill/linkedin-apply-for-agents/references/intake.md`: tell the user what files, facts, and preferences they still need to provide. Do not start searching or applying yet.
5. If the target location is missing, ask for it before searching or applying. If it is Hong Kong, tell the user that LinkedIn (Hong Kong geoId) and JobsDB will both be used; do not ask whether to include JobsDB. Never ask which platforms to use.
6. After materials are collected, complete login on the computer used for the run. The user may sign in themselves (cloud computer or their own computer), or give the agent the account password or another login method so it can complete the login flow there. Never write passwords back into the chat or into the skill.
7. Do not copy anyone else's resume, salary, visa, or screening rules into this install. Wait for the current user's materials.
