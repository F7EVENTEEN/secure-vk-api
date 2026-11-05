# Secure VK API Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. User explicitly requested implementation and GitHub publication; execute locally without additional design questions.

**Goal:** Repair security defaults in a separate attributed vk_api fork for the private music bot.

**Architecture:** Preserve upstream module layout. Add SafeSession and EncryptedConfig; change only authentication, persistence and diagnostics defaults. Test actual modified classes; mock only network sends.

**Tech Stack:** Python 3.13, unittest, requests, cryptography, beautifulsoup4, Docker Compose.

**Spec:** docs/SPEC.md

## Global Constraints

- Default config is memory-only; AES-256-GCM persistence is explicit.
- No borrowed OAuth application identity by default.
- HTTPS VK-only transport and bounded timeouts; TLS verification always on.
- No real account data in tests, Git or build context.
- Preserve Apache-2.0 and upstream attribution.

## Review Focus

- Requests prepared outside request() and cross-host redirects must still be validated.
- NaN/infinite/negative/custom timeout objects must not create unbounded requests.
- Errors during encrypted save must preserve the previous good state.
- Failed auth and debug helper must not leak or retain password/session.
- Default session, explicitly supplied session and disabled TLS paths must obey the same policy.

### Task 1: Auth and diagnostics

Files: vk_api/vk_api.py, vk_api/utils.py, tests/test_auth_security.py.
Interfaces: existing VkApi, auth(), enable_debug_mode(); no new public API.

- [x] Write tests for cookie/token logging, default MemoryConfig, AUDIO-only scope, explicit app_id and password removal on success/error.
- [x] Run `python -m unittest discover -s tests -v`; observe security failures against imported baseline.
- [x] Change defaults, remove sensitive log interpolations, require explicit app_id for OAuth, clear password in finally, disable HTTP debug dumps.
- [x] Run full suite, require zero failures, commit.

### Task 2: Encrypted persistence

Files: vk_api/secure_config.py, tests/test_secure_config.py.
Produces: EncryptedConfig(section, *, filename, key: bytes), compatible with VkApi(config=functools.partial(EncryptedConfig, key=key)).

- [x] Write roundtrip, ciphertext confidentiality, different nonce, invalid key/tampering/truncation and atomic-save-failure tests; observe missing feature failures.
- [x] Implement AESGCM, versioned binary envelope, same-directory private temporary file, fsync/os.replace, cleanup on error and fail-closed loading.
- [x] Run full suite, require zero failures, commit.

### Task 3: Transport

Files: vk_api/secure_transport.py, vk_api/vk_api.py, tests/test_transport.py.
Produces: SafeSession(requests.Session), validates every send() including redirect hops.

- [x] Write blocked-host/URL/TLS/timeout/redirect tests; observe missing feature failures.
- [x] Implement allowlist, TLS and finite positive timeout enforcement; set trust_env=False; make SafeSession the client default and reject arbitrary custom sessions.
- [x] Run full suite, require zero failures, commit.

### Task 4: Packaging and publication

Files: pyproject.toml, requirements.lock, Dockerfile, compose.yaml, README.md, SECURITY.md, NOTICE, .gitignore, .dockerignore, .github/workflows/tests.yml.

- [x] Pin and audit runtime dependencies, record advisory results; package/import smoke test including vk_api.audio.
- [x] Add nonroot Docker test image and Compose test service; validate Compose config, attempt image build only if Docker engine is available.
- [x] Run full suite and compile check; independent reviewer checks security delta, fix important findings with regression tests.
- [ ] Commit and publish private repository via authenticated GitHub tools; verify remote files/commit. If repository creation/auth is unavailable, complete local deliverable and report exact missing action.
