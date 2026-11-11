# Copyable team handoff prompt

Give your coding assistant this prompt with the repository URL. Replace the phase number and role as the project progresses. The team member needs access to the private repository through GitHub or a local clone.

```text
Repository: https://github.com/bharat0722/flipkart-ai-advisor
I am M2, the receiving lead for Phase 1 and the owner of Phase 2. Start with the receiving review in issue #4 and the Phase 2 work in issue #5. Carry out the Phase 1 receiving review and then implement Phase 2 once its prerequisite is accepted. Read AGENTS.md, docs/PRD.md, docs/phase_status.json, docs/architecture.md, the project plan PDF and the latest phase handoff. Inspect main, open PRs, milestone issues and prior review evidence before making changes.

Reproduce the predecessor from a fresh checkout using the documented inputs and commands. Compare actual hashes, counts and tests, and record the evidence and any coverage issue. If acceptance is pending, give me the evidence to review and ask for the specific decision required. Treat an approval as recorded only when it comes from the actual receiving lead. If access, credentials or data are missing, identify the concrete blocker and complete the independent setup work you can.

After predecessor acceptance, branch from current main. Implement the requested phase end to end against the approved requirements. Use real inputs, run the appropriate tests, and make setup and verification reproducible. Document any changed architecture, schema or configuration. Keep credentials, raw data, generated data and indexes out of Git.

Before review, write docs/handoffs/phase-02.md from the template with exact commands, observed results, issues, limitations and the next receiving lead. Update Phase 2 in docs/phase_status.json to ready_for_review and run python scripts/sync_prd.py to refresh docs/PRD.md. Run python scripts/sync_prd.py --check. Link the issue and milestone in the PR, include the handoff and verification evidence, and report the PR link and status. Leave acceptance to the next receiving lead. Stop after Phase 2.
```

For Phase 3, 4 or 5, change the role, predecessor, phase number and handoff filename. Use `docs/handoffs/TEMPLATE.md` and the relevant PRD section to determine the acceptance checks.
