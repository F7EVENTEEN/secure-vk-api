# SDD ledger — plan: docs/PLAN.md

Baseline imported from audited PyPI wheel 11.10.1. Three confidentiality failures reproduced offline against upstream. Python 3.13.6. Work occurs in a new, isolated repository on harden/security-defaults; no existing project branch is touched.

Ruling: latest user explicitly chose repairing the library rather than browser-first connector and requested implementation/publication. Implement that selected approach; keep bot spec as a future consumer. Cost: live VK auth may fail despite local security tests.

Pre-flight: Task 1 config interface is consumed by Task 2; retain jconfig-compatible constructor(section, filename=...). Task 3 replaces default transport consumed by auth/audio; CDN access intentionally excluded. Task 4 packages all three and must include audio optional imports.

GitHub connector authenticated as lodit. It supports file/Git writes but has no create-repository action. Existing Git credential returned HTTP 401. User asked asynchronously to provide a new empty private repository URL; independent implementation continues.
