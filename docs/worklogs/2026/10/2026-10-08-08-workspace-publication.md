# Workspace publication preparation

Changed: Grouped authorized workspace changes into runtime/diagnostics, Web/DeepSeek, data integrity/charts, and delivery/evidence commits. Added ignores for raw p9c3g/h/i runs.
Reason: User explicitly requested reasonable commits and remote push.
Validation: origin/main matched starting HEAD after fetch; diff checks passed; publishable-file credential/size scan passed; project key ignored and untracked. Prior V1 regression/evidence record remains authoritative. No new full-suite PASS is claimed in this publication increment.
Evidence: docs/reports/phase-09/V1_COMPLETION_REPORT.md; Git commit history; artifacts/logs/publication-groups.json (local grouping record).
Risk: Historical long-stability limits remain; publication does not expand acceptance.
Not Verified: Remote push confirmation is obtained after commits through Git remote ref comparison, not asserted here in advance.
Next Step: Push the authorized commits without force and compare local HEAD with origin/main; keep local credentials and raw assets outside Git.
