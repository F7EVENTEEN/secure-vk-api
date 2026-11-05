"""Explicit encrypted persistence for secure-vk-api (Apache-2.0).

The caller must protect the independent encryption key. Docker secrets are
mounts, not encryption of the host key file. Do not put that key beside state.
"""
import json
import os
from pathlib import Path
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jconfig.base import BaseConfig

MAGIC = b'SVK1'
MAX_STATE_BYTES = 2 * 1024 * 1024


class EncryptedConfig(BaseConfig):
    __slots__ = ('_filename', '_cipher')

    def __init__(self, section, *, filename, key):
        if not isinstance(key, bytes) or len(key) != 32:
            raise ValueError('An independent 32-byte encryption key is required')
        self._filename = Path(filename)
        self._cipher = AESGCM(key)
        super().__init__(section)

    def load(self, **kwargs):
        try:
            with self._filename.open('rb') as stream:
                envelope = stream.read(MAX_STATE_BYTES + 1)
        except FileNotFoundError:
            return {}
        if len(envelope) > MAX_STATE_BYTES or len(envelope) < 32 or not envelope.startswith(MAGIC):
            raise ValueError('Invalid encrypted session envelope')
        try:
            plaintext = self._cipher.decrypt(envelope[4:16], envelope[16:], MAGIC)
            settings = json.loads(plaintext)
        except (InvalidTag, ValueError, UnicodeError):
            raise ValueError('Cannot authenticate encrypted session state') from None
        if not isinstance(settings, dict) or any(not isinstance(v, dict) for v in settings.values()):
            raise ValueError('Invalid encrypted session structure')
        return settings

    def save(self):
        plaintext = json.dumps(self._settings, ensure_ascii=False).encode('utf-8')
        if len(plaintext) + 32 > MAX_STATE_BYTES:
            raise ValueError('Session state exceeds the storage limit')
        nonce = os.urandom(12)
        envelope = MAGIC + nonce + self._cipher.encrypt(nonce, plaintext, MAGIC)
        descriptor, temporary = tempfile.mkstemp(prefix='.secure-vk-', dir=self._filename.parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(envelope)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._filename)
        finally:
            # This is one exact file returned by mkstemp; never a recursive delete.
            if os.path.exists(temporary):
                os.unlink(temporary)
