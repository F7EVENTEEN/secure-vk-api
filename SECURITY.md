# Security scope

This is an experimental fork, not a claim of a comprehensive audit. Do not
introduce a real account until you understand the remaining constraints.

Fixed defaults are covered by offline tests: cookie/token logging, plaintext
default session storage, overbroad default OAuth scope, borrowed default app
identity, retained password attribute, debug HTTP dumping, unbounded timeouts,
TLS disabling and requests/redirects outside the VK HTTPS boundary.

EncryptedConfig uses AES-256-GCM with a fresh random nonce, authenticated
envelope and atomic replacement. Protect its separate 32-byte key with owner-only
filesystem permissions outside this repository. A readable key and ciphertext
together are sufficient to decrypt state. Docker Compose secrets do not encrypt
host files. A privileged host/container administrator can access process memory.
Python password attribute cleanup is not secure memory erasure.

Scope=AUDIO is only an OAuth request setting; it does not grant restricted audio
API access or constrain the power of browser cookies. Web session theft can
compromise the broader account. You must supply an explicit app_id you are
authorized to use; whether VK permits the required flow must be verified live.
No application identity is borrowed automatically.

The transport is intended for VK account endpoints, not the public Internet or
an arbitrary downloader. Unsupported CDN/Long Poll/upload hosts fail closed.
The allowlist is a hostname boundary, not a DNS-pinning implementation. VK domain
ownership, CA trust and the local resolver remain trust assumptions. Install no
third-party adapter or code that mutates the security boundary. Total-operation
deadlines are the consumer's responsibility: connect/read timeouts are not a
wall-clock transfer limit.

Do not enable HTTP debug logging in Requests/urllib3 or log raw exceptions,
request/response objects, session state or exception attributes. Legacy upstream
exceptions can retain request values for retry, and upstream response messages
are not a safe user-facing error format. The future bot must map errors to
fixed safe status codes and never dump upstream objects.

The remaining legacy modules are included for attribution/compatibility, not
fully audited. Generic uploads and websocket streaming have separate boundaries.
Legacy HTTP polling/upload helpers now also use SafeSession and reject unknown
hosts. The websocket streaming extension is not included as a runtime dependency
and has not been reviewed. Encrypted state replacement does not fsync the parent
directory; power-loss durability beyond the file fsync is not guaranteed.
No captcha bypass, alternate-account rotation, DRM bypass or global track
availability is implemented. Use only content you are permitted to obtain.

Do not file public reports containing session cookies or account data. Rotate
exposed credentials, revoke the VK session in VK settings and remove local state.
