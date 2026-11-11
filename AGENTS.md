# Working on Flipkart AI Electronics Advisor

Start with `docs/PRD.md`, `docs/architecture.md`, `docs/phase_status.json` and the previous phase's handoff. The original architecture and five-phase plan are in `docs/Flipkart_AI_Electronics_Advisor_Project_Plan.pdf`.

Implement only the phase requested. Base a focused branch on current `main` after confirming its predecessor was accepted. If acceptance or repository access is missing, report that dependency and prepare the parts you can complete safely. Use the real catalogue from the documented source and keep credentials, raw data, generated data and local indexes out of Git.

Before opening a PR, run the relevant checks, write `docs/handoffs/phase-NN.md` from the template, update that phase in `docs/phase_status.json` and run `python scripts/sync_prd.py`. Record actual test results, reproducible commands, limitations and the receiving lead. Use `ready_for_review` when your implementation and evidence are ready. The receiving lead records acceptance after independently reproducing the work. Keep GitHub issue and milestone references in the PR and handoff.

See `docs/HANDOFF_PROMPT.md` for the copyable kickoff prompt and `docs/github_workflow.md` for the team workflow.
