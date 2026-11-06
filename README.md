# secure-vk-api

Experimental security-focused fork of [python273/vk_api](https://github.com/python273/vk_api)
11.10.1, retaining the Apache-2.0 license and author notices. Distribution name:
`secure-vk-api`; Python import name: `vk_api`. Do not install alongside the
original distribution in the same environment.

Создан как отдельная библиотека для личного музыкального Telegram-бота.
Сам бот, база музыки и mini app ещё не реализованы. Доступность авторизации,
личных плейлистов, глобального поиска и файлов ВК ещё не проверена на аккаунте.
Исправления безопасности не открывают закрытый API ВК и не дают разрешения
скачивать любой трек.

## Что изменено

- Сессия по умолчанию остаётся в памяти; обычный JSON больше не создаётся.
- Для сохранения есть EncryptedConfig с AES-256-GCM и отдельным ключом.
- Убраны значения cookies, токенов и captcha из журналов; HTTP debug dump отключён.
- Пароль удаляется из атрибута после попытки auth; права по умолчанию — AUDIO.
- app_id нужно передать явно: автоматического использования чужого приложения нет.
- SafeSession разрешает только HTTPS ВК, проверяет каждый redirect, не позволяет
  отключить TLS, унаследовать proxy из окружения или убрать таймаут.

Это намеренно несовместимые изменения части upstream-поведения. Подробнее —
[SECURITY.md](SECURITY.md), [спецификация](docs/SPEC.md) и [план](docs/PLAN.md).

## Проверка без аккаунта

Python 3.13+, из корня проекта:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install --only-binary=:all: --require-hashes -r requirements.lock
.venv/Scripts/python -m unittest discover -s tests -v
```

Linux: вместо `.venv/Scripts/python` используй `.venv/bin/python`.

```sh
docker compose run --build --rm tests
```

Docker запускает только офлайн-тесты, без аккаунта, портов и runtime-секретов.
Контейнер непривилегированный, root filesystem read-only, сеть выключена на
время тестов. Docker Engine должен быть запущен. Это тестовая сборка библиотеки,
а не работающий музыкальный бот или сервер API.

## Использование библиотеки

Установка из исходников (пакет в PyPI этим проектом не публиковался):

```sh
git clone https://github.com/F7EVENTEEN/secure-vk-api.git
cd secure-vk-api
python -m pip install --only-binary=:all: --require-hashes -r requirements.lock
python -m pip install --no-deps .
```

Используй отдельное виртуальное окружение с Python 3.13+. Проверенные runtime
зависимости фиксируются lock-файлом; сборочный backend указан в pyproject.toml.

Для веб-доступа к музыке есть отдельный путь без app_id:

```python
from vk_api.audio import VkAudio
from vk_api.secure_transport import SafeSession

session = SafeSession()
# Cookies загружаются из собственной зашифрованной сессии после ручного входа
# на официальном сайте. Не пересылай и не публикуй их.
audio = VkAudio.from_session(session, user_id=your_numeric_vk_user_id)
```

Это конструктор для уже авторизованной сессии, не средство её получения.
Владелец должен подтвердить соответствие сессии своему профилю. app_id и ID
пользователя — разные вещи. Доступность музыки через сайт ещё требует живой
проверки; OAuth-пример ниже для этого пути не нужен.

```python
from vk_api import VkApi

# Токен получай только разрешённым для твоего приложения способом.
# В реальном коде загружай его из защищённого secret, не из исходника.
client = VkApi(token=token_from_secret)
profile = client.method('users.get')
```

Шифрованное хранение подключается явно:

```python
from functools import partial
from pathlib import Path
from vk_api import VkApi
from vk_api.secure_config import EncryptedConfig

key = Path('/run/secrets/vk_state_key').read_bytes()  # ровно 32 случайных байта
client = VkApi(
    login=login_from_local_input,
    password=password_from_getpass,
    app_id=your_authorized_app_id,
    config=partial(EncryptedConfig, key=key),
    config_filename='/runtime/vk-state.enc',
    auth_handler=your_local_2fa_handler,
)
# Авторизацию вызывай локально после проверки разрешённого VK flow.
# client.auth()
```

Сначала проверяется разрешённая авторизация с app_id владельца. Если этот flow
не поддерживает музыку, нельзя считать интеграцию готовой; потребуется другой
согласованный способ подключения. Не пересылай пароль, 2FA, token или cookies
в Telegram/чат, не передавай их сторонним сервисам скачивания.

Ключ генерируется случайно один раз, хранится вне проекта и отдельно от volume
сессии. На Windows ограничь ACL владельцем; на Linux — каталог 0700 и файл 0600.
Не сохраняй один ключ в образе/Compose/.env. Для переноса на сервер перемещай ключ
отдельным защищённым каналом; ВК может потребовать повторный вход.

## Что проверено

Результаты локальных тестов и dependency audit фиксируются в `docs/VERIFICATION.md`.
Тесты используют только вымышленные данные. Полная проверка всех legacy-модулей,
реальная авторизация ВК и скачивание аудио не выполнены. Образ Docker нельзя
считать проверенным только по успешному `docker compose config`.

Актуальная проверка музыки: чтение библиотеки (включая недоступные записи),
поиск, JSON-плейлисты и разрешение MP3 проверены на разрешённой браузерной
сессии. Метаданные доступны через `get_metadata_iter()` без загрузки аудио;
поле `available` обозначает доступность. Ссылки и хеши остаются в памяти.
Полный текущий набор — 61 синтетический тест. Часть CDN-ссылок Telegram
не принимает напрямую; доставку файла обеспечивает приложение-потребитель.
