#!/usr/bin/env python3
"""Собирает статический сайт migisweetlab.com из шаблонов ниже и src/*.md.

Запуск: python3 build.py   (нужен пакет markdown: pip install markdown)
Результат пишется прямо в корень репозитория (index.html, sortit/...), GitHub Pages
отдаёт его как есть. Править тексты политики — только в src/privacy-policy.*.md
(это те же файлы, что лежат в SortIt/docs/legal и в игре).
"""
from pathlib import Path
import re
import markdown

ROOT = Path(__file__).parent

# Ссылки на сторы: пока пусто — кнопка показывается как «Скоро».
APP_STORE_URL = ""   # например https://apps.apple.com/app/id0000000000
GOOGLE_PLAY_URL = ""  # https://play.google.com/store/apps/details?id=com.migisweetlab.sortit
EMAIL = "migisweetlab@gmail.com"
SITE = "https://migisweetlab.com"

APPLE_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.4 12.6c0-2.4 2-3.5 2-3.6-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.2-2.8.8-3.5.8-.7 0-1.8-.8-3-.8-1.5 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.4 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3 .7c1.3 0 2.1-1.1 2.8-2.3.9-1.3 1.3-2.6 1.3-2.6s-2.5-1-2.5-3.6zM14.2 5.6c.6-.8 1.1-1.9 1-3-1 0-2.1.7-2.8 1.5-.6.7-1.1 1.8-1 2.9 1 .1 2.1-.6 2.8-1.4z"/></svg>'
PLAY_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4 2.6c-.3.3-.4.7-.4 1.2v16.4c0 .5.1.9.4 1.2l9.2-9.4L4 2.6zm10.4 8.2 2.7-2.7L6.3 2c-.4-.2-.8-.3-1.1-.2l9.2 9zm0 2.4-9.2 9c.3.1.7 0 1.1-.2l10.8-6.1-2.7-2.7zm3.9-4.4-3 3 3 3 3.3-1.9c.9-.5.9-1.8 0-2.3l-3.3-1.8z"/></svg>'


def store_btn(url, svg, small, big):
    inner = f'{svg}<span><small>{small}</small>{big}</span>'
    if url:
        return f'<a class="btn" href="{url}" rel="noopener">{inner}</a>'
    return f'<span class="btn soon" title="Coming soon">{inner}</span>'


def page(title, desc, body, path, lang="en"):
    depth = path.count("/")
    up = "../" * depth
    canon = SITE + "/" + path.replace("index.html", "")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<link rel="icon" type="image/png" sizes="32x32" href="{up}assets/icon-32.png">
<link rel="apple-touch-icon" href="{up}assets/icon-180.png">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{SITE}/assets/icon-512.png">
<meta property="og:url" content="{canon}">
<meta name="theme-color" content="#ee6a2c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<div class="wrap">
<header class="top">
  <a class="brand" href="{up or './'}"><img src="{up}assets/icon-192.png" alt="">SortIt</a>
  <nav class="nav">
    <a href="{up}sortit/support/">Support</a>
    <a href="{up}sortit/privacy/">Privacy</a>
  </nav>
</header>
{body}
<footer>
  <span>© 2026 Migisweetlab</span>
  <span><a href="{up}sortit/privacy/">Privacy Policy</a> · <a href="{up}sortit/privacy/ru/">Конфиденциальность</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></span>
</footer>
</div>
</body>
</html>
"""


def write(path, html):
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", path)


def landing():
    stores = (store_btn(APP_STORE_URL, APPLE_SVG, "Download on the", "App Store")
              + store_btn(GOOGLE_PLAY_URL, PLAY_SVG, "Get it on", "Google Play"))
    soon = "" if (APP_STORE_URL and GOOGLE_PLAY_URL) else '<p style="margin-top:14px;font-size:14px">Coming soon to iPhone and Android.</p>'
    body = f"""
<section class="hero">
  <div>
    <img class="app-icon" src="assets/icon-512.png" alt="SortIt app icon" width="104" height="104">
    <h1>SortIt</h1>
    <p class="tag">Sort the shelves. Match three. Relax.</p>
    <p>A cozy goods-sorting puzzle: tap items on the shelves and put three of a kind together to clear them.
    300 levels, a new Daily level every day and 50 spicy Challenge levels — all playable offline.</p>
    <div class="stores">{stores}</div>
    {soon}
  </div>
  <div class="phone-pair" aria-hidden="true">
    <div class="phone a"><img src="assets/shot-home.webp" alt="" width="585" height="1266"></div>
    <div class="phone b"><img src="assets/shot-game.webp" alt="" width="585" height="1266"></div>
  </div>
</section>

<section class="features">
  <div class="feature"><div class="emo">🧺</div><h3>300 levels</h3><p>Six sets of 50 levels that grow from relaxing to tricky, with different shelf shapes along the way.</p></div>
  <div class="feature"><div class="emo">📅</div><h3>Daily level</h3><p>One fresh puzzle every day. Keep your streak going and collect rewards.</p></div>
  <div class="feature"><div class="emo">🌶️</div><h3>Challenge</h3><p>50 spicy levels with traps and boss stages for players who want a real puzzle.</p></div>
  <div class="feature"><div class="emo">🧲</div><h3>Helpful boosters</h3><p>Magnet, Freeze, Shuffle, Hint and Undo — earned with in-game coins, never with real money.</p></div>
  <div class="feature"><div class="emo">✈️</div><h3>Plays offline</h3><p>No account, no sign-in. Your progress stays on your phone.</p></div>
  <div class="feature"><div class="emo">🚫</div><h3>No ads</h3><p>No ads and no real-money purchases — just the puzzle.</p></div>
</section>

<h2 class="section">Screenshots</h2>
<div class="shots">
  <img src="assets/shot-game.webp" alt="Game screen with a shelf of items" width="585" height="1266" loading="lazy">
  <img src="assets/shot-shelves.webp" alt="Wall shelves level" width="585" height="1266" loading="lazy">
  <img src="assets/shot-home.webp" alt="Home screen with Daily level and Challenge" width="585" height="1266" loading="lazy">
  <img src="assets/shot-sets.webp" alt="Level sets" width="585" height="1266" loading="lazy">
</div>
<div style="height:32px"></div>
"""
    write("index.html", page("SortIt — cozy goods-sorting puzzle",
                             "Sort the shelves, match three and relax. 300 levels, a Daily level and Challenge mode. By Migisweetlab.",
                             body, "index.html"))
    # /sortit/ ведёт на главную, чтобы ссылка migisweetlab.com/sortit тоже работала
    write("sortit/index.html", f"""<!doctype html><meta charset="utf-8"><title>SortIt</title>
<link rel="canonical" href="{SITE}/"><meta http-equiv="refresh" content="0; url=../"><a href="../">SortIt</a>
""")


def policy(src, path, lang, other_href, other_label, title):
    md = (ROOT / "src" / src).read_text(encoding="utf-8")
    html = markdown.markdown(md, extensions=["extra", "sane_lists", "nl2br"])
    # голые URL → ссылки
    html = re.sub(r'(?<![">])(https://[^\s<]+)', r'<a href="\1" rel="noopener">\1</a>', html)
    html = html.replace(EMAIL, f'<a href="mailto:{EMAIL}">{EMAIL}</a>')
    body = f'<article class="doc"><a class="lang" href="{other_href}">{other_label}</a>{html}</article>'
    desc = "SortIt privacy policy" if lang == "en" else "Политика конфиденциальности SortIt"
    write(path, page(title, desc, body, path, lang))


def support():
    body = f"""
<article class="doc">
  <a class="lang" href="#ru">RU</a>
  <h1>Support</h1>
  <p>Questions, a bug, an idea for a level, or a level you can't beat? Write to us — we read every message.</p>
  <p style="font-size:20px;font-weight:900"><a href="mailto:{EMAIL}?subject=SortIt%20support">{EMAIL}</a></p>
  <p>To help us fix a problem faster, please include your device model, OS version, the game version (Settings, at the bottom) and the level number.</p>
  <h2>FAQ</h2>
  <p><b>Will I lose my progress if I change phones?</b><br>Progress is stored on your device. It moves to a new phone only through your phone's own backup (iCloud or Google backup).</p>
  <p><b>Does the game need the internet?</b><br>No, all levels are playable offline.</p>
  <p><b>How do I turn off analytics?</b><br>Settings → Analytics. See the <a href="../privacy/">Privacy Policy</a> for details.</p>
  <hr id="ru" style="border:none;border-top:2px solid var(--line);margin:34px 0 10px">
  <h1 style="font-size:28px">Поддержка</h1>
  <p>Вопрос, ошибка, идея или уровень, который не получается пройти? Напишите нам: <a href="mailto:{EMAIL}?subject=SortIt">{EMAIL}</a>. Укажите, пожалуйста, модель телефона, версию системы, версию игры (внизу экрана «Настройки») и номер уровня.</p>
  <p>Прогресс хранится на устройстве и переносится на новый телефон только через резервную копию (iCloud или Google). Аналитику можно выключить в «Настройки → Аналитика» — подробнее в <a href="../privacy/ru/">политике конфиденциальности</a>.</p>
</article>
"""
    write("sortit/support/index.html", page("SortIt — Support", "Contact Migisweetlab about SortIt.", body, "sortit/support/index.html"))


def not_found():
    body = '<article class="doc" style="text-align:center"><h1>Page not found</h1><p><a href="/">Back to SortIt</a></p></article>'
    html = page("Page not found — SortIt", "Page not found", body, "404.html")
    # 404 отдаётся с любого пути, поэтому пути абсолютные
    html = html.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')
    html = html.replace('href="sortit/', 'href="/sortit/').replace('href="./"', 'href="/"')
    write("404.html", html)


if __name__ == "__main__":
    landing()
    policy("privacy-policy.en.md", "sortit/privacy/index.html", "en", "ru/", "RU", "SortIt — Privacy Policy")
    policy("privacy-policy.ru.md", "sortit/privacy/ru/index.html", "ru", "../", "EN", "SortIt — Политика конфиденциальности")
    support()
    not_found()
