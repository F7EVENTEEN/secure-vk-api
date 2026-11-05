# SDD ledger — plan: docs/PLAN.md

Baseline imported from audited PyPI wheel 11.10.1. Three confidentiality failures reproduced offline against upstream. Python 3.13.6. Work occurs in a new, isolated repository on harden/security-defaults; no existing project branch is touched.

Ruling: latest user explicitly chose repairing the library rather than browser-first connector and requested implementation/publication. Implement that selected approach; keep bot spec as a future consumer. Cost: live VK auth may fail despite local security tests.

Pre-flight: Task 1 config interface is consumed by Task 2; retain jconfig-compatible constructor(section, filename=...). Task 3 replaces default transport consumed by auth/audio; CDN access intentionally excluded. Task 4 packages all three and must include audio optional imports.

GitHub connector authenticated as lodit. It supports file/Git writes but has no create-repository action. Existing Git credential returned HTTP 401. User asked asynchronously to provide a new empty private repository URL; independent implementation continues.

Update: user's personal GitHub connection is F7EVENTEEN. Explicit credential
selection for that account succeeds. Private repository F7EVENTEEN/secure-vk-api
created through the authenticated GitHub REST API; no code pushed before review.

Task 1: complete. 9 upstream failures observed, 10 tests passed after fixes.
Task 2: complete. 9 missing-feature failures observed, full suite 19/19 passed.
Task 3: complete. 12 missing-feature failures observed, full suite 31/31 passed.
Final review: important OTP diagnostic and legacy transport findings reproduced
as four failing regressions; fixed, complete suite 36/36 passed. Added audio import
smoke coverage, verification report and fork/upstream version distinction.
Final: minor (deferred): parent directory fsync after atomic replacement — file
contents are synced, power-loss durability beyond that is not guaranteed.
Ruling: Windows sandbox denies its AppData temp writes; test scratch defaults to
the known project directory, Docker explicitly uses /tmp. Build hook temp uses
workspace work/build-temp. No change to global TEMP or user Git TLS configuration.

Task 4 verification: 36/36 Windows tests and 36/36 Linux Docker tests pass. Wheel
build, compileall, pip check and Compose validation pass. Runtime audit has no
known vulnerabilities for all 11 pinned dependencies. Docker image digest and
CI action commit SHAs pinned. Repository created private in F7EVENTEEN account.
