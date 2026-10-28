# migisweetlab.com

Сайт студии Migisweetlab и игры SortIt. Хостинг — GitHub Pages, домен — Porkbun.

| Страница | URL |
|---|---|
| Игра (лендинг) | https://migisweetlab.com/ |
| Privacy Policy (en) | https://migisweetlab.com/sortit/privacy/ |
| Политика конфиденциальности (ru) | https://migisweetlab.com/sortit/privacy/ru/ |
| Support | https://migisweetlab.com/sortit/support/ |

## Как править
- Тексты политики — `src/privacy-policy.en.md` и `src/privacy-policy.ru.md` (держать в синхроне с `SortIt/docs/legal/` и копией в игре).
- Ссылки на сторы — `APP_STORE_URL` / `GOOGLE_PLAY_URL` в начале `build.py`.
- После правок: `pip install markdown && python3 build.py`, затем commit + push.
