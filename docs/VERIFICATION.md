# Verification — 2026-11-06

Environment: Python 3.13.6, Windows, isolated virtual environment. Tests contain
only synthetic credentials and do not call VK or a music CDN.

## Tests and TDD evidence

- Authentication tests: 9 failures reproduced against imported upstream baseline
  before changes; resulting authentication suite passes after fixes.
- Encrypted config: 9 missing-feature failures observed before implementation;
  confidentiality, roundtrip, nonce changes, key/tamper rejection and preservation
  of previous state on replacement failure pass afterward.
- Transport: 12 missing-feature failures observed before implementation;
  real Requests redirect logic is tested with only the wire adapter substituted.
- Independent review identified remaining OTP response logging and legacy HTTP
  helper bypasses. Four regression failures reproduced before fixes, then pass.
- Final suite: `python -m unittest discover -s tests -v`: 36 tests, 0 failures.
- Follow-up web-session constructor: 2 missing-feature failures reproduced,
  then fixed; current Windows suite has 38 passing tests. This path does not
  require an OAuth app_id and still needs live owner-session verification.
- Strict library snapshots: 4 regressions added for empty/missing batches and
  unresolvable source IDs. Current full suite has 42 passing tests; GitHub CI
  at c1ae6daa78f89c854a9f952e5aa52a90c2866eb5 passed, including Docker.
- `python -m compileall -q vk_api jconfig tests`: passes.
- Audio module import is exercised by the suite; fork/upstream versions are
  separately reported as `vk_api.__version__` and `__upstream_version__`.

## Dependencies and build

- 11 runtime dependencies pinned with published SHA-256 wheel hashes in
  requirements.lock. All platform wheel hashes are retained to permit Windows
  and Linux installation with `--only-binary=:all: --require-hashes`.
- `pip-audit --disable-pip --no-deps -r requirements.lock`: no known
  vulnerabilities found. Raw results: dependency-audit.json. Advisory databases
  change; this is not a guarantee of no unknown vulnerabilities.
- Source wheel builds successfully using setuptools 84.2.1. It includes both
  Apache-2.0 LICENSE and the fork NOTICE. Build tooling and Docker base image are
  not covered by the runtime dependency advisory result.
- `docker compose config --quiet`: passes.
- Docker Desktop was started locally. `docker compose run --build --rm tests`:
  image builds successfully; Linux container executes all 36 tests with 0 failures,
  with network disabled, nonroot UID and read-only root filesystem.
- Base image digest and GitHub Actions commit SHAs are pinned. Actions outcome
  must still be inspected after publication.

## Independent review

Reviewer examined the security delta from upstream baseline bc733d6, the new
modules, test cases, Docker and packaging. No critical issue reported; both
important findings were reproduced and fixed with regression tests. Parent
directory fsync was deferred: ordinary atomic replacement is covered, but
power-loss durability beyond file-content fsync is not promised.

## Still requires real-world verification

No real VK login, user-owned OAuth application compatibility, own-library read,
playlist read, global music search or audio download was tested. The original
bot spec is a proposal, not an implemented product. No application ID is borrowed
to conceal these unknowns. Complete that live checkpoint before building the
personal bot on this fork; if VK denies the flow, revisit the connector approach.
