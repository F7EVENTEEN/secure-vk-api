# Secure VK API fork: initial scope

User direction, 2026-11-06: repair the reviewed library and publish a separate GitHub project. This supersedes the browser-first recommendation in the music bot proposal. The personal Docker music bot remains the consumer; it is not implemented by this library release.

Base: python273/vk_api 11.10.1, Apache-2.0. Preserve attribution and mark modified files. Keep import name vk_api for compatibility; distribution name secure-vk-api, version 0.1.0. Do not claim an official VK API or a comprehensive security audit.

Alternatives considered: use upstream unchanged (rejected due demonstrated leaks), custom browser connector (more integration work, retained as fallback), maintained fork fixing defaults (explicitly selected by user).

Required behavior:

- Never log tokens, cookies, phone/login or captcha answers through library-generated log messages; debug HTTP dumping is disabled.
- Default config is memory-only. Optional EncryptedConfig saves authenticated AES-256-GCM ciphertext with independent 32-byte key; malformed/tampered state fails closed, never resets to plaintext. Atomic replacement; new nonce each save. Caller is responsible for key-file access control outside repo/images.
- Default OAuth scope requests AUDIO only, not sum of all permissions. Browser cookies still grant broader account access: scope does not constrain them.
- No borrowed OAuth application identity by default. Caller explicitly supplies their app_id if token acquisition is needed. Actual compatibility of audio access/auth with a user-owned app is a required live checkpoint, not guaranteed by tests.
- Password is removed from the client attribute after auth attempt, successful or not. Python cannot guarantee erasure of all memory copies. Credentials are never accepted over Telegram.
- SafeSession is the default transport: HTTPS only; exact vk.ru/vk.com or their subdomains, port 443 only, no URL userinfo. Validate each prepared request including redirects; TLS verification cannot be disabled. Connect/read timeouts default to 10/30 seconds; unbounded, negative, NaN or infinite timeouts are rejected. Environment proxies disabled by default. User-supplied sessions must also use SafeSession. This library is not the audio-CDN downloader; CDN and third-party upload URLs are rejected by default.
- No bypassing captcha or account blocks. Live credentials only after tests and user-facing limitations. No guarantee every track can be downloaded.
- Private GitHub repository by default. Never include account data, cookies, bot token or encryption keys. Docker/CI runs offline account-free tests, including audio module import smoke test. Docker daemon currently unavailable; report local image test as unverified unless it becomes available.

Explicitly out of scope: bot commands, music database, CDN downloading, mini app, public multi-user deployment, comprehensive review of every legacy VK endpoint. Unsupported operations fail rather than silently weakening transport policy. Runtime dependencies are pinned with hashes and checked for known advisories before publication.

Acceptance: original leak tests pass against modified source; encrypted persistence roundtrip/tamper/nonce/atomicity tested; redirects/TLS/timeouts blocked before network in tests; no credentials required for test run; independent review completed. Live VK authentication/search/music/download remains unverified until owner-authorized manual test.
