#!/usr/bin/env python3
"""Собирает статический сайт migisweetlab.com из шаблонов ниже и src/*.md.

Запуск: python3 build.py   (нужны пакеты markdown и Pillow: pip install markdown pillow)
        python3 build.py --check   — только проверить, что сайт совпадает с игрой (код выхода 1, если нет)
Результат пишется прямо в корень репозитория (index.html, sortit/...), GitHub Pages
отдаёт его как есть.

Источник правды — репозиторий игры (SORTIT_REPO, по умолчанию ../SortIt):
- политика конфиденциальности — копия той, что внутри игры
  (shared/src/commonMain/composeResources/files/legal/privacy_{en,ru}.md) → src/privacy-policy.*.md;
- скриншоты на лендинге — эталоны скриншот-тестов игры (SHOTS ниже) → assets/shot-*.webp.
Руками src/privacy-policy.*.md и assets/shot-*.webp не править: build.py перезапишет их из игры.
"""
from pathlib import Path
import io
import os
import re
import sys
try:
    import markdown  # если стоит — используем его
except ImportError:  # системный python3 на Маке: пакета нет, хватает встроенного конвертера
    markdown = None

ROOT = Path(__file__).parent
APP = Path(os.environ.get("SORTIT_REPO") or ROOT.parent / "SortIt").expanduser()
APP_LEGAL = "shared/src/commonMain/composeResources/files/legal"
APP_SNAPSHOTS = "shared/src/androidHostTest/snapshots"
POLICIES = {"privacy-policy.en.md": "privacy_en.md", "privacy-policy.ru.md": "privacy_ru.md"}
# Скриншот на сайте → эталон скриншот-теста игры (390×844 dp). Размер на сайте 585×1266.
SHOTS = {
    "shot-game.webp": "site:shots-src/game-level21.png",  # снят с телефона: у golden-а уровня 21 старая раскладка
    "shot-home.webp": "Home_challenge_open_390x844.png",
    "shot-sets.webp": "Packs_mid_390x844.png",
    "shot-shelves.webp": "Game_scheme20_390x844.png",
}
SHOT_SIZE = (585, 1266)
APP_LEVELS = "shared/src/commonMain/composeResources/files/levels"



def _inline(text: str) -> str:
    import html as _h
    t = _h.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return t


def md_to_html(md: str) -> str:
    """Минимальный Markdown для политики: # заголовки, абзацы (перевод строки → <br />), списки «- », **жирный**, ссылки."""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append("<p>" + "<br />\n".join(_inline(x) for x in para) + "</p>")
            para.clear()
        if items:
            out.append("<ul>\n" + "\n".join(f"<li>{_inline(x)}</li>" for x in items) + "\n</ul>")
            items.clear()

    for line in md.splitlines():
        s = line.rstrip()
        h = re.match(r"^(#{1,6})\s+(.*)$", s)
        li = re.match(r"^\s*[-*+]\s+(.*)$", s)
        if not s.strip():
            flush()
        elif h:
            flush()
            n = len(h.group(1))
            out.append(f"<h{n}>{_inline(h.group(2))}</h{n}>")
        elif li:
            if para:
                flush()
            items.append(li.group(1))
        else:
            if items:
                flush()
            para.append(s.strip())
    flush()
    return "\n".join(out)

def level_counts():
    """Сколько уровней в игре — считаем файлы, а не пишем числа руками."""
    base = APP / APP_LEVELS
    n = lambda pattern: sum(1 for p in base.glob(pattern) if p.name != "index.json")
    packs = sorted(base.glob("pack_*"))
    return {"line": n("pack_*/*.json"), "packs": len(packs),
            "per_pack": n(f"{packs[0].name}/*.json") if packs else 0,
            "zen": n("zen/*.json"), "challenge": n("challenge/*.json")}

# Ссылки на сторы: пока пусто — кнопка показывается как «Скоро».
APP_STORE_URL = ""   # например https://apps.apple.com/app/id0000000000
GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details?id=com.migisweetlab.sortit"
# Provider token из App Store Connect (Analytics → Campaigns). Если задан, к ссылке
# в App Store добавляются pt/ct — установки видны по кампаниям (ct = ?src= из ссылки).
APP_STORE_PT = ""
EMAIL = "migisweetlab@gmail.com"
SITE = "https://migisweetlab.com"

APPLE_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.4 12.6c0-2.4 2-3.5 2-3.6-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.2-2.8.8-3.5.8-.7 0-1.8-.8-3-.8-1.5 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.4 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3 .7c1.3 0 2.1-1.1 2.8-2.3.9-1.3 1.3-2.6 1.3-2.6s-2.5-1-2.5-3.6zM14.2 5.6c.6-.8 1.1-1.9 1-3-1 0-2.1.7-2.8 1.5-.6.7-1.1 1.8-1 2.9 1 .1 2.1-.6 2.8-1.4z"/></svg>'
PLAY_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4 2.6c-.3.3-.4.7-.4 1.2v16.4c0 .5.1.9.4 1.2l9.2-9.4L4 2.6zm10.4 8.2 2.7-2.7L6.3 2c-.4-.2-.8-.3-1.1-.2l9.2 9zm0 2.4-9.2 9c.3.1.7 0 1.1-.2l10.8-6.1-2.7-2.7zm3.9-4.4-3 3 3 3 3.3-1.9c.9-.5.9-1.8 0-2.3l-3.3-1.8z"/></svg>'


SETS = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}


def synced_files():
    """Файлы сайта, которые берутся из игры: путь → байты."""
    from PIL import Image
    if not (APP / APP_LEGAL).is_dir():
        sys.exit(f"Не нашёл репозиторий игры: {APP} (задай SORTIT_REPO)")
    out = {}
    for site_name, app_name in POLICIES.items():
        out[f"src/{site_name}"] = (APP / APP_LEGAL / app_name).read_bytes()
    for site_name, golden in SHOTS.items():
        src = ROOT / golden[5:] if golden.startswith("site:") else APP / APP_SNAPSHOTS / golden
        im = Image.open(src).convert("RGB").resize(SHOT_SIZE, Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=88, method=6)
        out[f"assets/{site_name}"] = buf.getvalue()
    return out


def sync_from_app(check=False):
    """Скопировать из игры политику и скриншоты. check=True — только сравнить. Возвращает список отличий."""
    stale = []
    for rel, data in synced_files().items():
        path = ROOT / rel
        if rel.endswith(".md"):
            same = path.exists() and path.read_bytes() == data
        else:  # картинка: сравниваем пиксели, а не байты кодека
            same = path.exists() and _same_pixels(path, data)
        if not same:
            stale.append(rel)
            if not check:
                path.write_bytes(data)
    return stale


def _same_pixels(path, data, tol=2.0):
    from PIL import Image, ImageChops, ImageStat
    a = Image.open(path).convert("RGB")
    b = Image.open(io.BytesIO(data)).convert("RGB")
    if a.size != b.size:
        return False
    return max(ImageStat.Stat(ImageChops.difference(a, b)).mean) <= tol


def store_btn(url, svg, small, big):
    inner = f'{svg}<span><small>{small}</small>{big}</span>'
    if url:
        return f'<a class="btn" href="{url}" rel="noopener">{inner}</a>'
    return f'<span class="btn soon" title="Coming soon">{inner}</span>'


def page(title, desc, body, path, lang="en", head=""):
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
{head}</head>
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
  <span><a href="{up}sortit/privacy/">Privacy Policy</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></span>
</footer>
</div>
</body>
</html>
"""


CHECK_ONLY = False
STALE_PAGES = []


def write(path, html):
    out = ROOT / path
    if CHECK_ONLY:  # --check: страница отличается от того, что собралось бы сейчас
        if not out.exists() or out.read_text(encoding="utf-8") != html:
            STALE_PAGES.append(path)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", path)


def landing():
    c = level_counts()
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
    {c["line"]} levels, {c["zen"]} relaxing Zen levels without a timer, a new Daily level every day
    and {c["challenge"]} spicy Challenge levels — all playable offline.</p>
    <div class="stores">{stores}</div>
    {soon}
  </div>
  <div class="phone-pair" aria-hidden="true">
    <div class="phone a"><img src="assets/shot-home.webp" alt="" width="585" height="1266"></div>
    <div class="phone b"><img src="assets/shot-game.webp" alt="" width="585" height="1266"></div>
  </div>
</section>

<section class="features">
  <div class="feature"><div class="emo">🧺</div><h3>{c["line"]} levels</h3><p>{SETS.get(c["packs"], c["packs"])} sets of {c["per_pack"]} levels that grow from relaxing to tricky, with different shelf shapes along the way.</p></div>
  <div class="feature"><div class="emo">📅</div><h3>Daily level</h3><p>One fresh puzzle every day. Keep your streak going and collect rewards.</p></div>
  <div class="feature"><div class="emo">🌶️</div><h3>Challenge</h3><p>{c["challenge"]} spicy levels with traps and boss stages for players who want a real puzzle.</p></div>
  <div class="feature"><div class="emo">🍃</div><h3>Zen</h3><p>{c["zen"]} calm levels with no timer. Sort at your own pace and relax.</p></div>
  <div class="feature"><div class="emo">🧲</div><h3>Helpful boosters</h3><p>Magnet, Freeze, Shuffle, Hint and Undo — earned with in-game coins, never with real money.</p></div>
  <div class="feature"><div class="emo">✈️</div><h3>Offline, no ads</h3><p>No account, no ads, no real-money purchases. Your progress stays on your phone.</p></div>
</section>

<h2 class="section">Screenshots</h2>
<div class="shots">
  <img src="assets/shot-game.webp" alt="Level 21: shelves full of snacks and drinks" width="585" height="1266" loading="lazy">
  <img src="assets/shot-shelves.webp" alt="Wall shelves level" width="585" height="1266" loading="lazy">
  <img src="assets/shot-home.webp" alt="Home screen with Daily level and Challenge" width="585" height="1266" loading="lazy">
  <img src="assets/shot-sets.webp" alt="Level sets" width="585" height="1266" loading="lazy">
</div>
<div style="height:32px"></div>
"""
    write("index.html", page("SortIt — cozy goods-sorting puzzle",
                             f"Sort the shelves, match three and relax. {c['line']} levels, Zen, a Daily level and Challenge mode. By Migisweetlab.",
                             body, "index.html"))
    # /sortit/ ведёт на главную, чтобы ссылка migisweetlab.com/sortit тоже работала
    write("sortit/index.html", f"""<!doctype html><meta charset="utf-8"><title>SortIt</title>
<link rel="canonical" href="{SITE}/"><meta http-equiv="refresh" content="0; url=../"><a href="../">SortIt</a>
""")


def get_page():
    """/sortit/get/ — ссылка для шеринга из игры: отправляет в стор по ОС телефона.

    GitHub Pages — статика, поэтому ОС определяется скриптом в браузере. Превью в
    мессенджерах берётся из OG-тегов (боты скрипт не выполняют). Android → Google Play,
    iPhone/iPad → App Store; если ссылки на стор ещё нет или это компьютер — остаёмся
    на странице с кнопками. Параметр ?src=… (по умолчанию share) уходит в стор как
    метка источника: utm_source в referrer Google Play и ct в App Store (если задан pt).
    """
    script = f"""<script>
(function () {{
  var APP_STORE = {APP_STORE_URL!r}, PLAY = {GOOGLE_PLAY_URL!r}, PT = {APP_STORE_PT!r};
  var ua = navigator.userAgent || "";
  // iPadOS 13+ представляется Маком: отличаем по сенсорному экрану
  var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 0);
  var android = /Android/i.test(ua);
  var src = "share";
  try {{ src = (new URLSearchParams(location.search).get("src") || "share").replace(/[^\\w-]/g, "").slice(0, 40) || "share"; }} catch (e) {{}}
  var url = "";
  if (android && PLAY) {{
    url = PLAY + (PLAY.indexOf("?") < 0 ? "?" : "&") + "referrer=" + encodeURIComponent("utm_source=" + src + "&utm_medium=link");
  }} else if (ios && APP_STORE) {{
    url = APP_STORE;
    if (PT) url += (url.indexOf("?") < 0 ? "?" : "&") + "pt=" + PT + "&ct=" + src + "&mt=8";
  }}
  if (url) {{ document.documentElement.className += " redirecting"; location.replace(url); }}
}})();
</script>
<style>.redirecting .get-hero {{ visibility: hidden; }}</style>
"""
    stores = (store_btn(APP_STORE_URL, APPLE_SVG, "Download on the", "App Store")
              + store_btn(GOOGLE_PLAY_URL, PLAY_SVG, "Get it on", "Google Play"))
    soon = "" if (APP_STORE_URL and GOOGLE_PLAY_URL) else '<p style="margin-top:14px;font-size:14px">Coming soon to iPhone and Android.</p>'
    body = f"""
<section class="hero get-hero" style="text-align:center;display:block">
  <img class="app-icon" style="margin-left:auto;margin-right:auto" src="../../assets/icon-512.png" alt="SortIt app icon" width="104" height="104">
  <h1>Play SortIt</h1>
  <p class="tag">Sort the shelves. Match three. Relax.</p>
  <p>A cozy goods-sorting puzzle with a new Daily level every day. Free, no ads, plays offline.</p>
  <div class="stores" style="justify-content:center">{stores}</div>
  {soon}
  <p style="margin-top:18px;font-size:14px"><a href="../../">More about the game</a></p>
</section>
"""
    write("sortit/get/index.html", page("Play SortIt — cozy goods-sorting puzzle",
                                        "Sort the shelves, match three and relax. Get SortIt for iPhone and Android.",
                                        body, "sortit/get/index.html", head=script))


def policy(src, path, lang, title):
    md = (ROOT / "src" / src).read_text(encoding="utf-8")
    html = (markdown.markdown(md, extensions=["extra", "sane_lists", "nl2br"]) if markdown
            else md_to_html(md))
    # голые URL → ссылки
    html = re.sub(r'(?<![">])(https://[^\s<]+)', r'<a href="\1" rel="noopener">\1</a>', html)
    html = html.replace(EMAIL, f'<a href="mailto:{EMAIL}">{EMAIL}</a>')
    body = f'<article class="doc">{html}</article>'
    desc = "SortIt privacy policy" if lang == "en" else "Политика конфиденциальности SortIt"
    write(path, page(title, desc, body, path, lang))


def support():
    body = f"""
<article class="doc">
  <h1>Support</h1>
  <p>Questions, a bug, an idea for a level, or a level you can't beat? Write to us — we read every message.</p>
  <p style="font-size:20px;font-weight:900"><a href="mailto:{EMAIL}?subject=SortIt%20support">{EMAIL}</a></p>
  <p>To help us fix a problem faster, please include your device model, OS version, the game version (Settings, at the bottom) and the level number.</p>
  <h2>FAQ</h2>
  <p><b>Will I lose my progress if I change phones?</b><br>Progress is stored on your device. It moves to a new phone only through your phone's own backup (iCloud or Google backup).</p>
  <p><b>Does the game need the internet?</b><br>No, all levels are playable offline.</p>
  <p><b>How do I turn off analytics?</b><br>Settings → Analytics. See the <a href="../privacy/">Privacy Policy</a> for details.</p>
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


def build_pages():
    landing()
    policy("privacy-policy.en.md", "sortit/privacy/index.html", "en", "SortIt — Privacy Policy")
    # Русская версия пока не публикуется: старый адрес ведёт на английскую
    write("sortit/privacy/ru/index.html", f"""<!doctype html><meta charset="utf-8"><title>SortIt — Privacy Policy</title>
<link rel="canonical" href="{SITE}/sortit/privacy/"><meta http-equiv="refresh" content="0; url=../"><a href="../">Privacy Policy</a>
""")
    support()
    get_page()
    not_found()


if __name__ == "__main__":
    if "--check" in sys.argv:
        stale = sync_from_app(check=True)
        if not stale:  # страницы сравниваем, только когда исходники уже совпадают
            CHECK_ONLY = True
            build_pages()
            stale = STALE_PAGES
        if stale:
            print("Сайт отстаёт от игры: " + ", ".join(stale) + "\nОбновить: python3 build.py")
            sys.exit(1)
        print("Сайт совпадает с игрой.")
        sys.exit(0)
    updated = sync_from_app()
    print("Из игры обновлено: " + (", ".join(updated) if updated else "ничего"))
    build_pages()
