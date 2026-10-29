# migisweetlab.com

Сайт студии Migisweetlab и игры SortIt. Хостинг — GitHub Pages, домен — Porkbun.

| Страница | URL |
|---|---|
| Игра (лендинг) | https://migisweetlab.com/ |
| Privacy Policy (en) | https://migisweetlab.com/sortit/privacy/ |
| Support | https://migisweetlab.com/sortit/support/ |

## Как править
- Политика и скриншоты берутся из игры: `build.py` копирует `privacy_{en,ru}.md` из `SortIt/shared/.../files/legal/` в `src/` и делает `assets/shot-*.webp` из эталонов скриншот-тестов (таблица `SHOTS` в `build.py`). Руками их не править — править в игре.
- Числа уровней (линейка, Дзен, Испытание, размер наборов) `build.py` считает по файлам уровней игры — руками не писать.
- Проверить, что сайт не отстал от игры: `python3 build.py --check` (код 1 — отстал). Путь к игре — `SORTIT_REPO`, по умолчанию `../SortIt`.
- После merge тикета SortIt, который меняет политику, спрайты товаров или эти эталоны, раннер agent-team сам запускает `build.py`, коммитит и пушит сайт (`after_merge` в `projects/sortit/project.yaml`).
- Ссылки на сторы — `APP_STORE_URL` / `GOOGLE_PLAY_URL` в начале `build.py`.
- После правок: `pip install markdown pillow && python3 build.py`, затем commit + push.
