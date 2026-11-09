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

# --- Local Safe (репозиторий LocalVault) ---
# Источник правды — репозиторий приложения (LOCALVAULT_REPO, по умолчанию ../LocalVault):
# - политика — строки privacy_* из composeResources/values{,-ru}/strings.xml → src/localsafe-privacy.*.md;
# - скриншоты — эталоны Roborazzi (LS_SHOTS) → assets/localsafe/shot-*.webp;
# - иконки — iOS-иконка 1024 → assets/localsafe/icon-*.png.
# Если репозитория нет (например, сайт собирается после тикета SortIt на другой машине),
# эти файлы просто не обновляются — берутся те, что уже лежат в сайте.
LV = Path(os.environ.get("LOCALVAULT_REPO") or ROOT.parent / "LocalVault").expanduser()
LV_STRINGS = {"en": "shared/src/commonMain/composeResources/values/strings.xml",
              "ru": "shared/src/commonMain/composeResources/values-ru/strings.xml"}
LV_SNAPSHOTS = "shared/src/androidHostTest/snapshots"
LV_ICON = "iosApp/iosApp/Assets.xcassets/AppIcon.appiconset/app-icon-1024.png"
LS_SHOTS = {  # эталон 720×1280 → 540×960 на сайте; {L} — English / Russian
    "shot-start": "StartScreenshotTest.startScreenWithRecents{L}.png",
    "shot-entry": "EntryScreenshotTest.entryPasswordShown{L}.png",
    "shot-docs": "EntryFormScreenshotTest.documentKindPicker{L}.png",
    "shot-unlock": "UnlockScreenshotTest.unlockWithBiometrics{L}.png",
}
LS_SHOT_SIZE = (540, 960)
LS_NAME = "Local Safe"
# Ссылки на сторы Local Safe: пока пусто — кнопка «Скоро».
LS_APP_STORE_URL = ""  # https://apps.apple.com/app/id<Apple ID из App Store Connect → App Information>
LS_GOOGLE_PLAY_URL = ""  # https://play.google.com/store/apps/details?id=com.migisweetlab.vault — вписать после публикации
# Пока сторов нет — бета: тестирование Google Play (кнопка «Стать тестировщиком») и публичная ссылка TestFlight.
LS_PLAY_TESTING_URL = "https://play.google.com/apps/testing/com.migisweetlab.vault"
LS_TESTFLIGHT_URL = ""  # https://testflight.apple.com/join/<код> — публичная ссылка из App Store Connect → TestFlight
# Дата вступления политики в силу (в приложении пока плейсхолдер — подставляем свою).
LS_POLICY_DATE = {"en": "9 November 2026", "ru": "9 ноября 2026 г."}
KEEPASSXC_URL = "https://keepassxc.org/"
KEEPASSXC_BROWSER_URL = "https://chromewebstore.google.com/detail/keepassxc-browser/oboonakemofpalcgghocfoadofidjkkk"



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
# Закрытое тестирование Google Play: по этой ссылке тестер нажимает «Стать тестировщиком».
PLAY_TESTING_URL = "https://play.google.com/apps/testing/com.migisweetlab.sortit"
TESTFLIGHT_URL = "https://testflight.apple.com/join/M5Xz6TdV"  # публичная ссылка TestFlight (iOS-бета), пока нет APP_STORE_URL
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
    out.update(localsafe_files())
    return out


def _android_string(raw: str) -> str:
    """Текст строкового ресурса Android/Compose → обычный текст."""
    return (raw.replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n").strip())


def localsafe_policy_md(lang: str) -> str:
    """Политика Local Safe в Markdown из строк приложения (тот же текст, что на экране «Политика»)."""
    import xml.etree.ElementTree as ET
    root = ET.parse(LV / LV_STRINGS[lang]).getroot()
    s = {e.get("name"): _android_string("".join(e.itertext())) for e in root.findall("string")}
    sections = ["collection", "storage", "password", "biometrics", "permissions", "photos",
                "autofill", "backup", "deletion", "contact"]  # порядок как в PrivacyPolicySection.kt
    date = s["privacy_effective_date"]
    if "[" in date:  # в приложении плейсхолдер
        date = ("Effective date: " if lang == "en" else "Дата вступления в силу: ") + LS_POLICY_DATE[lang]
    lines = [f"# {LS_NAME} — {s['privacy_title']}", "", date, "", s["privacy_intro"], ""]
    for key in sections:
        body = s[f"privacy_{key}_body"]
        if key == "contact" and body.startswith("["):
            body = ("Questions about this policy: " if lang == "en" else "Вопросы об этой политике: ") + EMAIL
        lines += [f"## {s[f'privacy_{key}_title']}", "", body, ""]
    # Приложение переименовано в Local Safe (09.11.2026); пока строки в нём не обновлены — меняем здесь.
    return "\n".join(lines).replace("LocalVault", LS_NAME)


def localsafe_files():
    """Файлы сайта из репозитория LocalVault: путь → байты. Пусто, если репозитория нет."""
    from PIL import Image
    if not (LV / LV_STRINGS["en"]).is_file():
        print(f"Нет репозитория LocalVault ({LV}): Local Safe не обновляю (задай LOCALVAULT_REPO)")
        return {}
    out = {}
    for lang in ("en", "ru"):
        out[f"src/localsafe-privacy.{lang}.md"] = localsafe_policy_md(lang).encode("utf-8")
    for name, golden in LS_SHOTS.items():
        for lang, word in (("en", "English"), ("ru", "Russian")):
            im = Image.open(LV / LV_SNAPSHOTS / golden.format(L=word)).convert("RGB")
            im = im.resize(LS_SHOT_SIZE, Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=88, method=6)
            out[f"assets/localsafe/{name}.{lang}.webp"] = buf.getvalue()
    icon = Image.open(LV / LV_ICON).convert("RGB")
    for size in (32, 180, 192, 512):
        buf = io.BytesIO()
        icon.resize((size, size), Image.LANCZOS).save(buf, "PNG", optimize=True)
        out[f"assets/localsafe/icon-{size}.png"] = buf.getvalue()
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
                path.parent.mkdir(parents=True, exist_ok=True)
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


def ios_btn():
    """App Store, если игра уже там; до этого — бета в TestFlight (значок «Download on the App Store»
    Apple разрешает только для опубликованных приложений); иначе «Скоро»."""
    if APP_STORE_URL:
        return store_btn(APP_STORE_URL, APPLE_SVG, "Download on the", "App Store")
    if TESTFLIGHT_URL:
        return store_btn(TESTFLIGHT_URL, APPLE_SVG, "iPhone beta on", "TestFlight")
    return store_btn("", APPLE_SVG, "Download on the", "App Store")


NUNITO = "family=Nunito:wght@400;700;800;900"
MANROPE = "family=Manrope:wght@500;700;800"
# Шапка, иконки и цвета страницы — по продукту. Пути от корня сайта.
SORTIT = dict(name="SortIt", home="sortit/", icon="assets/icon", theme="#ee6a2c", body="", font=NUNITO,
              nav=[("sortit/support/", "Support"), ("sortit/privacy/", "Privacy")], privacy="sortit/privacy/")
LOCALSAFE = dict(name=LS_NAME, home="localsafe/", icon="assets/localsafe/icon", theme="#0B1522", body="ls",
                 font=MANROPE, nav=[("localsafe/support/", "Help"), ("localsafe/privacy/", "Privacy"),
                                    ("localsafe/ru/", "RU")],
                 privacy="localsafe/privacy/")
LOCALSAFE_RU = dict(LOCALSAFE, home="localsafe/ru/", nav=[("localsafe/ru/support/", "Помощь"),
                                                          ("localsafe/privacy/ru/", "Политика"),
                                                          ("localsafe/", "EN")],
                    privacy="localsafe/privacy/ru/")
STUDIO = dict(name="Migisweetlab", home="", icon="assets/icon", theme="#0B0D12", body="studio",
              font=MANROPE, nav=[("sortit/", "SortIt"), ("localsafe/", LS_NAME)], privacy="")


def page(title, desc, body, path, lang="en", head="", product=SORTIT):
    depth = path.count("/")
    up = "../" * depth
    canon = SITE + "/" + path.replace("index.html", "")
    p = product
    brand_img = "" if p is STUDIO else f'<img src="{up}{p["icon"]}-192.png" alt="">'
    nav = "\n".join(f'    <a href="{up}{href}">{label}</a>' for href, label in p["nav"])
    privacy = (f'<a href="{up}{p["privacy"]}">{"Политика конфиденциальности" if lang == "ru" else "Privacy Policy"}</a> · '
               if p["privacy"] else "")
    apps = "" if p is STUDIO else f' · <a href="{up or "./"}">{"Все приложения" if lang == "ru" else "All apps"}</a>'
    body_cls = f' class="{p["body"]}"' if p["body"] else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<link rel="icon" type="image/png" sizes="32x32" href="{up}{p["icon"]}-32.png">
<link rel="apple-touch-icon" href="{up}{p["icon"]}-180.png">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{SITE}/{p["icon"]}-512.png">
<meta property="og:url" content="{canon}">
<meta name="theme-color" content="{p["theme"]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{p["font"]}&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
{head}</head>
<body{body_cls}>
<div class="wrap">
<header class="top">
  <a class="brand" href="{up}{p["home"] or './'}">{brand_img}{p["name"]}</a>
  <nav class="nav">
{nav}
  </nav>
</header>
{body}
<footer>
  <span>© 2026 <a href="{up or './'}">Migisweetlab</a>{apps}</span>
  <span>{privacy}<a href="mailto:{EMAIL}">{EMAIL}</a></span>
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
    stores = ios_btn() + store_btn(GOOGLE_PLAY_URL, PLAY_SVG, "Get it on", "Google Play")
    soon = "" if ((APP_STORE_URL or TESTFLIGHT_URL) and GOOGLE_PLAY_URL) else '<p style="margin-top:14px;font-size:14px">Coming soon to iPhone and Android.</p>'
    body = f"""
<section class="hero">
  <div>
    <img class="app-icon" src="../assets/icon-512.png" alt="SortIt app icon" width="104" height="104">
    <h1>SortIt</h1>
    <p class="tag">Sort the shelves. Match three. Relax.</p>
    <p>A cozy goods-sorting puzzle: tap items on the shelves and put three of a kind together to clear them.
    {c["line"]} levels, {c["zen"]} relaxing Zen levels without a timer, a new Daily level every day
    and {c["challenge"]} spicy Challenge levels — all playable offline.</p>
    <div class="stores">{stores}</div>
    {soon}
  </div>
  <div class="phone-pair" aria-hidden="true">
    <div class="phone a"><img src="../assets/shot-home.webp" alt="" width="585" height="1266"></div>
    <div class="phone b"><img src="../assets/shot-game.webp" alt="" width="585" height="1266"></div>
  </div>
</section>

<section class="features">
  <div class="feature"><div class="emo">🧺</div><h3>{c["line"]} levels</h3><p>{SETS.get(c["packs"], c["packs"])} sets of {c["per_pack"]} levels that grow from relaxing to tricky, with different shelf shapes along the way.</p></div>
  <div class="feature"><div class="emo">📅</div><h3>Daily level</h3><p>One fresh puzzle every day. Keep your streak going and collect rewards.</p></div>
  <div class="feature"><div class="emo">🌶️</div><h3>Challenge</h3><p>{c["challenge"]} spicy levels with traps and boss stages for players who want a real puzzle.</p></div>
  <div class="feature"><div class="emo">🍃</div><h3>Zen</h3><p>{c["zen"]} calm levels with no timer. Sort at your own pace and relax.</p></div>
  <div class="feature"><div class="emo">🧲</div><h3>Helpful boosters</h3><p>Magnet, Freeze, Shuffle, Hint and Undo — earned with in-game coins — there are no in-app purchases.</p></div>
  <div class="feature"><div class="emo">✈️</div><h3>Offline, no ads</h3><p>No account, no ads, no in-app purchases. Your progress stays on your phone.</p></div>
</section>

<h2 class="section">Screenshots</h2>
<div class="shots">
  <img src="../assets/shot-game.webp" alt="Level 21: shelves full of snacks and drinks" width="585" height="1266" loading="lazy">
  <img src="../assets/shot-shelves.webp" alt="Wall shelves level" width="585" height="1266" loading="lazy">
  <img src="../assets/shot-home.webp" alt="Home screen with Daily level and Challenge" width="585" height="1266" loading="lazy">
  <img src="../assets/shot-sets.webp" alt="Level sets" width="585" height="1266" loading="lazy">
</div>
<div style="height:32px"></div>
"""
    write("sortit/index.html", page("SortIt — cozy goods-sorting puzzle",
                                    f"Sort the shelves, match three and relax. {c['line']} levels, Zen, a Daily level and Challenge mode. By Migisweetlab.",
                                    body, "sortit/index.html"))


def studio_home():
    """/ — витрина студии (направление B, 09.11.2026): две большие плитки приложений. Лендинги — /sortit/ и /localsafe/."""
    body = f"""
<section class="studio-hero">
  <h1>Two apps. No ads. Made in London.</h1>
  <p>A one-person studio making small apps for iPhone and Android in the evenings.</p>
</section>
<section class="apps">
  <a class="app-tile sortit-tile" href="sortit/">
    <span class="app-head">
      <img src="assets/icon-512.png" alt="" width="64" height="64">
      <span><small>Puzzle game</small><b>SortIt</b></span>
    </span>
    <span class="app-line">Sort the shelves. Match three. Relax.</span>
    <span class="app-go" aria-hidden="true">{ICON_ARROW}</span>
    <span class="app-phone"><img src="assets/shot-game.webp" alt="A SortIt level" width="585" height="1266" loading="lazy"></span>
  </a>
  <a class="app-tile ls-tile-home" href="localsafe/">
    <span class="app-head">
      <img src="assets/localsafe/icon-512.png" alt="" width="64" height="64">
      <span><small>Password &amp; document vault</small><b>{LS_NAME}</b></span>
    </span>
    <span class="app-line">Passwords off the sticky notes and into an encrypted vault. Documents and photos fit in too.</span>
    <span class="app-go" aria-hidden="true">{ICON_ARROW}</span>
    <span class="app-phone"><img src="assets/localsafe/shot-entry.en.webp" alt="A saved login in {LS_NAME}" width="540" height="960" loading="lazy"></span>
  </a>
</section>
"""
    write("index.html", page("Migisweetlab — small apps for iPhone and Android",
                             f"Migisweetlab makes SortIt, a cozy sorting puzzle, and {LS_NAME}, an offline vault for passwords and documents.",
                             body, "index.html", product=STUDIO))


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
  var APP_STORE = {APP_STORE_URL!r}, PLAY = {GOOGLE_PLAY_URL!r}, PT = {APP_STORE_PT!r}, TF = {TESTFLIGHT_URL!r};
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
  }} else if (ios && TF) {{
    url = TF;
  }}
  if (url) {{ document.documentElement.className += " redirecting"; location.replace(url); }}
}})();
</script>
<style>.redirecting .get-hero {{ visibility: hidden; }}</style>
"""
    stores = ios_btn() + store_btn(GOOGLE_PLAY_URL, PLAY_SVG, "Get it on", "Google Play")
    soon = "" if ((APP_STORE_URL or TESTFLIGHT_URL) and GOOGLE_PLAY_URL) else '<p style="margin-top:14px;font-size:14px">Coming soon to iPhone and Android.</p>'
    body = f"""
<section class="hero get-hero" style="text-align:center;display:block">
  <img class="app-icon" style="margin-left:auto;margin-right:auto" src="../../assets/icon-512.png" alt="SortIt app icon" width="104" height="104">
  <h1>Play SortIt</h1>
  <p class="tag">Sort the shelves. Match three. Relax.</p>
  <p>A cozy goods-sorting puzzle with a new Daily level every day. No ads, no in-app purchases, plays offline.</p>
  <div class="stores" style="justify-content:center">{stores}</div>
  {soon}
  <p style="margin-top:18px;font-size:14px"><a href="../">More about the game</a></p>
</section>
"""
    write("sortit/get/index.html", page("Play SortIt — cozy goods-sorting puzzle",
                                        "Sort the shelves, match three and relax. Get SortIt for iPhone and Android.",
                                        body, "sortit/get/index.html", head=script))


def beta_page():
    """/sortit/beta/ — приглашение знакомых в закрытый тест: три кнопки по порядку, минимум текста.

    Промокоды больше не нужны (03.11.2026): два шага — стать тестировщиком и установить. Старые ссылки
    с ?code=… просто открывают эту же страницу. Gmail тестировщика владелец заранее добавляет в список в Play Console.
    APK тут намеренно нет: Google засчитывает тестера (12 человек × 14 дней), только если игра
    поставлена из Google Play под тем же аккаунтом, что нажал «Стать тестировщиком»."""
    def step(n_cls, small, big, href, extra=""):
        return (f'<p class="stores"><a class="btn{extra}" href="{href}" rel="noopener">{PLAY_SVG}'
                f'<span><small class="{n_cls}">{small}</small>{big}</span></a></p>')

    def block(lang):
        ru = lang == "ru"
        return "\n".join([
            ("  <h1>Помоги протестировать SortIt</h1>" if ru else '  <h1 style="font-size:30px">Help me test SortIt</h1>'),
            "  <p>" + ("Пара нажатий — и иногда заходи поиграть в течение 14 дней. Не удаляй игру, пожалуйста: так Google разрешит её выпустить. Спасибо!" if ru
                      else "A couple of taps — then play now and then for 14 days. Please don't uninstall it: that's how Google lets the game go live. Thank you!") + "</p>",
            "  " + step("n1", "Шаг 1" if ru else "Step 1", "Стать тестировщиком" if ru else "Become a tester", PLAY_TESTING_URL),
            "  " + step("n-install", "Шаг 2" if ru else "Step 2", "Установить из Google Play" if ru else "Install from Google Play",
                        GOOGLE_PLAY_URL),
            ('  <h2 style="margin-top:28px">' + ("На iPhone" if ru else "On iPhone") + "</h2>\n"
             + "  <p>" + ("Открой ссылку на iPhone, поставь TestFlight и нажми «Принять» → «Установить»." if ru
                          else "Open the link on your iPhone, get TestFlight, then tap Accept → Install.") + "</p>\n"
             + f'  <p class="stores"><a class="btn" href="{TESTFLIGHT_URL}" rel="noopener">{APPLE_SVG}'
             + "<span><small>" + ("Бета для iPhone" if ru else "iPhone beta") + "</small>TestFlight</span></a></p>"
             if TESTFLIGHT_URL else ""),
            '  <p style="font-size:14px;opacity:.75">' + ("Если Google Play пишет, что приложение недоступно, — напиши мне, я добавлю твою почту Gmail в список тестировщиков." if ru
                      else "If Google Play says the app isn't available, message me and I'll add your Gmail to the tester list.") + "</p>",
        ])

    body = f"""
<article class="doc beta">
  <a class="lang" href="#en">EN</a>
  <img class="app-icon" src="../../assets/icon-512.png" alt="SortIt app icon" width="88" height="88" style="width:88px;height:88px">
{block("ru")}
  <hr id="en" style="border:none;border-top:2px solid var(--line);margin:34px 0 10px">
{block("en")}
</article>
"""
    script = ""
    html = page("SortIt — бета-тест",
                "Помоги протестировать SortIt: пара нажатий в Google Play.",
                body, "sortit/beta/index.html", lang="ru", head=script)
    # Страница для знакомых владельца: почту в подвале не показываем
    html = html.replace(f' · <a href="mailto:{EMAIL}">{EMAIL}</a>', "")
    write("sortit/beta/index.html", html)


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
    body = '<article class="doc" style="text-align:center"><h1>Page not found</h1><p><a href="/">Back to Migisweetlab</a></p></article>'
    html = page("Page not found — Migisweetlab", "Page not found", body, "404.html", product=STUDIO)
    # 404 отдаётся с любого пути, поэтому пути абсолютные
    html = html.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')
    html = html.replace('href="sortit/', 'href="/sortit/').replace('href="localsafe/', 'href="/localsafe/')
    html = html.replace('href="./"', 'href="/"')
    write("404.html", html)


# ---------------------------------------------------------------- Local Safe

LS_TEXT = {
    "en": dict(
        tag="Your passwords and documents. Offline, on your phone.",
        lead=("An encrypted vault for passwords, bank cards, notes and documents — passports, ID cards, "
              "driving licences. No account, no cloud of ours, no tracking: the app has no internet access at all. "
              "Everything lives in one KeePass file that you own. Free, with no ads."),
        soon="Coming soon to iPhone and Android.",
        beta=("Beta. On Android, tap Become a tester, then install from Google Play. "
              f'If Play says the app isn’t available, <a href="mailto:{EMAIL}">write to us</a> and we’ll add your Gmail.'),
        beta_android=("Android beta: tap Become a tester, then install from Google Play. iPhone is coming soon. "
                      f'If Play says the app isn’t available, <a href="mailto:{EMAIL}">write to us</a>.'),
        title=f"{LS_NAME} — offline vault for passwords and documents",
        desc=(f"{LS_NAME} keeps passwords, bank cards and documents like passports in one encrypted KeePass file "
              "on your phone. No internet access, no account, no ads. For iPhone and Android."),
        help_h="Help",
        help_intro="Questions, a bug, or a document template your country is missing? Write to us — we read every message.",
        help_tip=("Please include your phone model, OS version and app version (Settings, at the bottom). "
                  "Never send us your master password or vault file."),
        faq=[
            ("I forgot my master password. Can you recover it?",
             "No. The master password is never stored, and the vault can't be opened without it — not by us, not by anyone. "
             "Keep it somewhere safe, for example written down at home."),
            ("How do I turn on autofill on iPhone?",
             "Open <b>Settings → General → AutoFill &amp; Passwords</b> and turn on Local Safe (on iOS 17: "
             "<b>Settings → Passwords → Password Options</b>)."),
            ("How do I turn on autofill on Android and in Chrome?",
             "Open Local Safe <b>Settings → Autofill</b> and choose it as the autofill service (in Android settings this "
             "is usually <b>Passwords, passkeys &amp; accounts → Preferred service</b>). Then in Chrome open "
             "<b>⋮ → Settings → Autofill services</b>, choose <b>Autofill using another service</b> and restart Chrome."),
            ("Can I use my vault on a computer?",
             'Yes — open the same file in KeePassXC and use the KeePassXC-Browser extension in Chrome. '
             'See <a href="{home}#desktop">the steps</a>.'),
            ("How do I sync between my phone and other devices?",
             "Keep the vault file in iCloud Drive, Google Drive or another synced folder and open it from there. "
             "The cloud app syncs the file; Local Safe re-reads it and merges changes before every save."),
            ("How do I back up my vault?",
             "Your vault is one .kdbx file. Copy it somewhere safe from time to time — a computer, a USB stick or a second "
             "cloud. Cloud drives also keep older versions of the file."),
            ("I used Safe+ (mySafebox). How do I move my data?",
             "Open <b>Settings → Import → Safe+</b>. On Android choose the folder <code>mySafeboxPro/DB</code> in the phone "
             "storage. On iPhone first copy the DB folder to the Files app, then choose it."),
            ("Does the app need the internet?",
             "No. It has no network code, no analytics and no ads. Syncing is done by your cloud app, not by Local Safe."),
            ("Is it free?", "Yes. No ads and no subscription."),
        ],
        faq_h="FAQ",
        policy_desc=f"{LS_NAME} privacy policy",
        get_h=f"Get {LS_NAME}",
        more="More about the app",
    ),
    "ru": dict(
        tag="Пароли и документы. Без интернета, на вашем телефоне.",
        lead=("Зашифрованный сейф для паролей, банковских карт, заметок и документов — паспортов, удостоверений, "
              "водительских прав. Без аккаунта, без нашего облака и без слежки: у приложения вообще нет доступа "
              "в интернет. Всё хранится в одном файле KeePass, и он ваш. Бесплатно и без рекламы."),
        soon="Скоро для iPhone и Android.",
        beta=("Бета. На Android нажмите «Стать тестировщиком», затем установите из Google Play. "
              f'Если Play пишет, что приложение недоступно, <a href="mailto:{EMAIL}">напишите нам</a> — добавим ваш Gmail.'),
        beta_android=("Бета для Android: нажмите «Стать тестировщиком», затем установите из Google Play. iPhone — скоро. "
                      f'Если Play пишет, что приложение недоступно, <a href="mailto:{EMAIL}">напишите нам</a>.'),
        title=f"{LS_NAME} — офлайн-сейф для паролей и документов",
        desc=(f"{LS_NAME} хранит пароли, банковские карты и документы вроде паспорта в одном зашифрованном файле KeePass "
              "на телефоне. Без интернета, без аккаунта, без рекламы. Для iPhone и Android."),
        help_h="Помощь",
        help_intro="Вопрос, ошибка или нет шаблона документа вашей страны? Напишите нам — читаем каждое письмо.",
        help_tip=("Укажите модель телефона, версию системы и версию приложения (внизу «Настроек»). "
                  "Никогда не присылайте мастер-пароль или файл сейфа."),
        faq=[
            ("Я забыл мастер-пароль. Можно его восстановить?",
             "Нет. Мастер-пароль нигде не хранится, и без него сейф не открыть — ни нам, ни кому-либо ещё. "
             "Храните его в надёжном месте, например записанным дома."),
            ("Как включить автозаполнение на iPhone?",
             "Откройте <b>Настройки → Основные → Автозаполнение и пароли</b> и включите Local Safe (в iOS 17 — "
             "<b>Настройки → Пароли → Параметры паролей</b>)."),
            ("Как включить автозаполнение на Android и в Chrome?",
             "В Local Safe откройте <b>Настройки → Автозаполнение</b> и выберите его службой автозаполнения (в настройках "
             "Android это обычно <b>Пароли, ключи доступа и аккаунты → Предпочтительный сервис</b>). Затем в Chrome: "
             "<b>⋮ → Настройки → Службы автозаполнения</b>, выберите <b>Автозаполнение с помощью другого сервиса</b> "
             "и перезапустите Chrome."),
            ("Можно ли пользоваться сейфом на компьютере?",
             'Да — откройте тот же файл в KeePassXC и подключите расширение KeePassXC-Browser в Chrome. '
             '<a href="{home}#desktop">Как это сделать</a>.'),
            ("Как синхронизировать телефон и другие устройства?",
             "Держите файл сейфа в iCloud Drive, Google Диске или другой синхронизируемой папке и открывайте его оттуда. "
             "Файл синхронизирует облачное приложение, а Local Safe перед каждым сохранением перечитывает его и сливает изменения."),
            ("Как сделать резервную копию?",
             "Сейф — один файл .kdbx. Время от времени копируйте его в надёжное место: на компьютер, флешку или во второе облако. "
             "Облачные диски к тому же хранят старые версии файла."),
            ("Я пользовался Safe+ (mySafebox). Как перенести данные?",
             "Откройте <b>Настройки → Импорт → Safe+</b>. На Android выберите папку <code>mySafeboxPro/DB</code> в памяти "
             "телефона. На iPhone сначала скопируйте папку DB в приложение «Файлы», затем выберите её."),
            ("Приложению нужен интернет?",
             "Нет. В нём нет сетевого кода, аналитики и рекламы. Синхронизацию делает ваше облачное приложение, а не Local Safe."),
            ("Это бесплатно?", "Да. Без рекламы и без подписки."),
        ],
        faq_h="Вопросы и ответы",
        policy_desc=f"Политика конфиденциальности {LS_NAME}",
        get_h=f"Скачать {LS_NAME}",
        more="Подробнее о приложении",
    ),
}


def ls_stores(lang):
    """App Store / Google Play, если приложение там уже есть; до этого — бета (TestFlight, тестирование Play);
    иначе «Скоро». Значки «Download on the App Store» / «Get it on Google Play» — только для опубликованного."""
    ru = lang == "ru"
    if LS_APP_STORE_URL:
        ios = store_btn(LS_APP_STORE_URL, APPLE_SVG, "Загрузите в" if ru else "Download on the", "App Store")
    elif LS_TESTFLIGHT_URL:
        ios = store_btn(LS_TESTFLIGHT_URL, APPLE_SVG, "Бета для iPhone" if ru else "iPhone beta on", "TestFlight")
    else:
        ios = store_btn("", APPLE_SVG, "Загрузите в" if ru else "Download on the", "App Store")
    if LS_GOOGLE_PLAY_URL:
        android = store_btn(LS_GOOGLE_PLAY_URL, PLAY_SVG, "Доступно в" if ru else "Get it on", "Google Play")
    else:
        android = store_btn(LS_PLAY_TESTING_URL, PLAY_SVG, "Бета для Android" if ru else "Android beta on", "Google Play")
    return ios + android


def ls_soon(lang, t):
    if LS_APP_STORE_URL and LS_GOOGLE_PLAY_URL:
        return ""
    if LS_APP_STORE_URL or LS_TESTFLIGHT_URL:
        return f'<p class="soon-note">{t["beta"]}</p>'
    if LS_GOOGLE_PLAY_URL or LS_PLAY_TESTING_URL:
        return f'<p class="soon-note">{t["beta_android"]}</p>'
    return f'<p class="soon-note">{t["soon"]}</p>'


# Landing copy (direction B, 09.11.2026): passwords first, then documents, cards and photos.
LS_LANDING = {
    "en": dict(
        h1='Your passwords deserve better than <span class="brass">a sticky note.</span>',
        lead=("Keep every login in one encrypted vault on your phone, unlock it with your face or fingerprint, "
              "and let it fill passwords in for you. No account, no internet access."),
        meta="Free · iPhone and Android",
        nb_kicker="From the notebook to the vault",
        nb_h="The notebook by the router has had a good run.",
        nb_paper="On paper or in Notes",
        nb_paper_items=["Anyone who finds it can read it",
                        "Lost with the bag, the phone case or the drawer",
                        "You still type every password by hand",
                        "Short, reused passwords because long ones don’t fit"],
        nb_safe=f"In {LS_NAME}",
        nb_safe_items=["Encrypted with AES-256 — unreadable without your master password",
                       "A backup copy is one file you can keep anywhere",
                       "Logins fill in apps and websites by themselves",
                       "A generator makes a long, unique password for every site"],
        nb_import=("Already saved them in Chrome or another app? Import them in a minute: Chrome, Apple Passwords, "
                   "Firefox, Bitwarden, 1Password, LastPass, KeePassXC and Safe+."),
        docs_kicker="And while you’re at it",
        docs_h="Documents, cards and photos — encrypted the same way.",
        docs_p=("Your passport number, driving licence, bank cards, a scan of the insurance letter. "
                "Everything sits in the same vault, behind the same master password."),
        docs_tiles=[("Documents", "Passport, ID and licence templates with the right fields"),
                    ("Bank cards", "Number, expiry, CVV and PIN, hidden until you tap"),
                    ("Photos and scans", "Attach images and PDFs to any entry, encrypted inside the file"),
                    ("Secure notes", "Wi-Fi codes, door codes, anything else")],
        docs_alt=["Choosing a document type"],
        never_kicker="What it never does",
        never_h="Trust you can check before you install.",
        never_p="Look at the permissions on Google Play or the privacy label on the App Store: there is nothing to see.",
        never_items=["Connects to the internet", "Asks you to make an account", "Stores your master password",
                     "Shows ads or tracks you", "Locks your data into its own format"],
        flow_h="Phone, cloud, computer",
        flow=[("On your phone", "Create a vault, unlock with Face ID or a fingerprint, autofill in apps and browsers."),
              ("In your cloud", f"Keep the .kdbx file in iCloud Drive or Google Drive. {LS_NAME} merges changes before it saves."),
              ("On your computer", 'Open the same file in <a href="{kx}" rel="noopener">KeePassXC</a>; '
                                   '<a href="{kxb}" rel="noopener">KeePassXC-Browser</a> fills logins in Chrome.')],
        flow_note=("On the computer: in KeePassXC open <b>Tools → Settings → Browser Integration</b> and tick Chrome, "
                   "then press <b>Connect</b> in the extension. KeePassXC is a free open-source project, "
                   "not affiliated with Migisweetlab."),
        sp_h="Moving from Safe+?",
        sp_p="Import your mySafebox database in a minute — folders, fields and attachments.",
        sp_btn="How to move",
        hero_alt=["Unlock with biometrics", "A saved login with the password shown", "Start screen"],
    ),
    "ru": dict(
        h1='Паролям нужно место надёжнее, чем <span class="brass">бумажка.</span>',
        lead=("Храните все логины в одном зашифрованном сейфе на телефоне, открывайте его лицом или отпечатком — "
              "пароли подставятся сами. Без аккаунта и без доступа в интернет."),
        meta="Бесплатно · iPhone и Android",
        nb_kicker="От блокнота к сейфу",
        nb_h="Блокнот у роутера своё отслужил.",
        nb_paper="На бумаге или в Заметках",
        nb_paper_items=["Прочитает любой, кто найдёт",
                        "Теряется вместе с сумкой, чехлом или ящиком стола",
                        "Каждый пароль всё равно вводите руками",
                        "Короткие и одинаковые пароли — длинные не помещаются"],
        nb_safe=f"В {LS_NAME}",
        nb_safe_items=["Зашифровано AES-256 — без мастер-пароля не прочитать",
                       "Резервная копия — один файл, храните где удобно",
                       "Логины сами подставляются в приложениях и на сайтах",
                       "Генератор придумает длинный уникальный пароль для каждого сайта"],
        nb_import=("Пароли уже в Chrome или другом приложении? Перенесите за минуту: Chrome, «Пароли» Apple, "
                   "Firefox, Bitwarden, 1Password, LastPass, KeePassXC и Safe+."),
        docs_kicker="А заодно",
        docs_h="Документы, карты и фото — зашифрованы так же.",
        docs_p=("Номер паспорта, права, банковские карты, скан страховки. "
                "Всё лежит в том же сейфе, за тем же мастер-паролем."),
        docs_tiles=[("Документы", "Шаблоны паспорта, ID и прав с нужными полями"),
                    ("Банковские карты", "Номер, срок, CVV и PIN скрыты до касания"),
                    ("Фото и сканы", "Картинки и PDF в любой записи, внутри зашифрованного файла"),
                    ("Заметки", "Коды от Wi-Fi и домофона, всё остальное")],
        docs_alt=["Выбор вида документа"],
        never_kicker="Чего оно никогда не делает",
        never_h="Доверие, которое можно проверить до установки.",
        never_p="Посмотрите разрешения в Google Play или ярлык конфиденциальности в App Store — там пусто.",
        never_items=["Выходит в интернет", "Просит завести аккаунт", "Хранит ваш мастер-пароль",
                     "Показывает рекламу или следит", "Запирает данные в своём формате"],
        flow_h="Телефон, облако, компьютер",
        flow=[("На телефоне", "Создайте сейф, открывайте по Face ID или отпечатку, автозаполнение в приложениях и браузерах."),
              ("В облаке", f"Держите файл .kdbx в iCloud Drive или Google Диске. Перед сохранением {LS_NAME} сливает изменения."),
              ("На компьютере", 'Откройте тот же файл в <a href="{kx}" rel="noopener">KeePassXC</a>; '
                                '<a href="{kxb}" rel="noopener">KeePassXC-Browser</a> подставит логины в Chrome.')],
        flow_note=("На компьютере: в KeePassXC откройте <b>Инструменты → Настройки → Интеграция с браузером</b>, "
                   "отметьте Chrome и нажмите <b>Connect</b> в расширении. KeePassXC — бесплатный проект "
                   "с открытым кодом, не связанный с Migisweetlab."),
        sp_h="Переезжаете с Safe+?",
        sp_p="Импортируйте базу mySafebox за минуту — папки, поля и вложения.",
        sp_btn="Как перенести",
        hero_alt=["Вход по биометрии", "Логин с открытым паролем", "Стартовый экран"],
    ),
}

ICON_X = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
          'aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>')
ICON_V = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>')
ICON_ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M9 7h8v8"/></svg>')


def ls_landing(lang):
    t, c = LS_TEXT[lang], LS_LANDING[lang]
    path = "localsafe/index.html" if lang == "en" else "localsafe/ru/index.html"
    up = "../" * path.count("/")
    a = f"{up}assets/localsafe/"
    help_href = "support/"
    li = lambda icon, text: f"<li>{icon}<span>{text}</span></li>"
    paper = "\n".join(li(ICON_X, s) for s in c["nb_paper_items"])
    safe = "\n".join(li(ICON_V, s) for s in c["nb_safe_items"])
    never = "\n".join(li(ICON_X, s) for s in c["never_items"])
    tiles = "\n".join(f'<div class="ls-tile"><b>{h}</b><span>{p}</span></div>' for h, p in c["docs_tiles"])
    flow = "\n".join(f'<div class="ls-step"><span class="n">{i}</span><b>{h}</b>'
                     f'<span>{p.format(kx=KEEPASSXC_URL, kxb=KEEPASSXC_BROWSER_URL)}</span></div>'
                     for i, (h, p) in enumerate(c["flow"], 1))
    hero_shots = [("unlock", "side l"), ("entry", "main"), ("start", "side r")]
    fan = "\n".join(f'<div class="ls-phone {cls}"><img src="{a}shot-{n}.{lang}.webp" alt="{alt}" width="540" height="960"></div>'
                    for (n, cls), alt in zip(hero_shots, c["hero_alt"]))
    body = f"""
<section class="ls-hero">
  <img class="ls-hero-icon" src="{a}icon-512.png" alt="{LS_NAME} app icon" width="112" height="112">
  <h1>{c["h1"]}</h1>
  <p class="lead">{c["lead"]}</p>
  <div class="stores">{ls_stores(lang)}</div>
  {ls_soon(lang, t)}
  <p class="meta">{c["meta"]}</p>
  <div class="ls-fan">
{fan}
  </div>
</section>
</div>

<div class="ls-band">
<div class="wrap">
<section class="ls-section">
  <p class="kicker">{c["nb_kicker"]}</p>
  <h2>{c["nb_h"]}</h2>
  <div class="ls-compare">
    <div class="ls-col paper"><h3>{c["nb_paper"]}</h3><ul class="ls-list">
{paper}
    </ul></div>
    <div class="ls-col safe"><h3>{c["nb_safe"]}</h3><ul class="ls-list">
{safe}
    </ul></div>
  </div>
  <p class="ls-note">{c["nb_import"]}</p>
</section>

<section class="ls-section ls-split">
  <div>
    <p class="kicker">{c["docs_kicker"]}</p>
    <h2>{c["docs_h"]}</h2>
    <p class="ls-p">{c["docs_p"]}</p>
    <div class="ls-tiles">
{tiles}
    </div>
  </div>
  <div class="ls-duo">
    <div class="ls-phone"><img src="{a}shot-docs.{lang}.webp" alt="{c["docs_alt"][0]}" width="540" height="960" loading="lazy"></div>
  </div>
</section>
</div>
</div>

<div class="ls-band deep">
<div class="wrap">
<section class="ls-section ls-split">
  <div>
    <p class="kicker">{c["never_kicker"]}</p>
    <h2>{c["never_h"]}</h2>
    <p class="ls-p">{c["never_p"]}</p>
  </div>
  <ul class="ls-never">
{never}
  </ul>
</section>
</div>
</div>

<div class="wrap">
<section class="ls-section" id="desktop">
  <h2>{c["flow_h"]}</h2>
  <div class="ls-steps">
{flow}
  </div>
  <p class="ls-note">{c["flow_note"].format(kx=KEEPASSXC_URL, kxb=KEEPASSXC_BROWSER_URL)}</p>
</section>

<section class="ls-cta">
  <div><h2>{c["sp_h"]}</h2><p>{c["sp_p"]}</p></div>
  <a href="{help_href}">{c["sp_btn"]}</a>
</section>
"""
    write(path, page(t["title"], t["desc"], body, path, lang=lang,
                     product=LOCALSAFE if lang == "en" else LOCALSAFE_RU))


def ls_support(lang):
    t = LS_TEXT[lang]
    path = "localsafe/support/index.html" if lang == "en" else "localsafe/ru/support/index.html"
    home = "../" if lang == "en" else "../"
    faq = "\n".join(f"  <p><b>{q}</b><br>{a.format(home=home)}</p>" for q, a in t["faq"])
    subject = "Local%20Safe%20support"
    body = f"""
<article class="doc">
  <h1>{t["help_h"]}</h1>
  <p>{t["help_intro"]}</p>
  <p style="font-size:20px;font-weight:800"><a href="mailto:{EMAIL}?subject={subject}">{EMAIL}</a></p>
  <p>{t["help_tip"]}</p>
  <h2>{t["faq_h"]}</h2>
{faq}
</article>
"""
    write(path, page(f"{LS_NAME} — {t['help_h']}", t["help_intro"], body, path, lang=lang,
                     product=LOCALSAFE if lang == "en" else LOCALSAFE_RU))


def ls_policy(lang):
    t = LS_TEXT[lang]
    path = "localsafe/privacy/index.html" if lang == "en" else "localsafe/privacy/ru/index.html"
    md = (ROOT / "src" / f"localsafe-privacy.{lang}.md").read_text(encoding="utf-8")
    html = (markdown.markdown(md, extensions=["extra", "sane_lists", "nl2br"]) if markdown else md_to_html(md))
    html = html.replace(EMAIL, f'<a href="mailto:{EMAIL}">{EMAIL}</a>')
    other = ('<a class="lang" href="ru/">RU</a>' if lang == "en" else '<a class="lang" href="../">EN</a>')
    title = md.splitlines()[0].lstrip("# ").strip()
    write(path, page(title, t["policy_desc"], f'<article class="doc">{other}{html}</article>', path, lang=lang,
                     product=LOCALSAFE if lang == "en" else LOCALSAFE_RU))


def ls_get_page():
    """/localsafe/get/ — одна ссылка на оба стора: отправляет по ОС телефона, иначе показывает кнопки."""
    t = LS_TEXT["en"]
    script = f"""<script>
(function () {{
  var APP_STORE = {LS_APP_STORE_URL or LS_TESTFLIGHT_URL!r}, PLAY = {LS_GOOGLE_PLAY_URL or LS_PLAY_TESTING_URL!r};
  var ua = navigator.userAgent || "";
  var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 0);
  var android = /Android/i.test(ua);
  var src = "share";
  try {{ src = (new URLSearchParams(location.search).get("src") || "share").replace(/[^\\w-]/g, "").slice(0, 40) || "share"; }} catch (e) {{}}
  var url = "";
  if (android && PLAY) url = PLAY + (PLAY.indexOf("?") < 0 ? "?" : "&") + "referrer=" + encodeURIComponent("utm_source=" + src + "&utm_medium=link");
  else if (ios && APP_STORE) url = APP_STORE;
  if (url) {{ document.documentElement.className += " redirecting"; location.replace(url); }}
}})();
</script>
<style>.redirecting .get-hero {{ visibility: hidden; }}</style>
"""
    body = f"""
<section class="hero get-hero" style="text-align:center;display:block">
  <img class="app-icon" style="margin-left:auto;margin-right:auto" src="../../assets/localsafe/icon-512.png" alt="{LS_NAME} app icon" width="104" height="104">
  <h1>{t["get_h"]}</h1>
  <p class="tag">{t["tag"]}</p>
  <div class="stores" style="justify-content:center">{ls_stores("en")}</div>
  {ls_soon("en", t)}
  <p style="margin-top:18px;font-size:14px"><a href="../">{t["more"]}</a></p>
</section>
"""
    write("localsafe/get/index.html", page(t["get_h"], t["desc"], body, "localsafe/get/index.html",
                                           head=script, product=LOCALSAFE))


def localsafe_pages():
    if not (ROOT / "src" / "localsafe-privacy.en.md").exists():
        print("Нет src/localsafe-privacy.*.md — страницы Local Safe пропущены")
        return
    for lang in ("en", "ru"):
        ls_landing(lang)
        ls_support(lang)
        ls_policy(lang)
    ls_get_page()


def build_pages():
    studio_home()
    landing()
    localsafe_pages()
    policy("privacy-policy.en.md", "sortit/privacy/index.html", "en", "SortIt — Privacy Policy")
    # Русская версия пока не публикуется: старый адрес ведёт на английскую
    write("sortit/privacy/ru/index.html", f"""<!doctype html><meta charset="utf-8"><title>SortIt — Privacy Policy</title>
<link rel="canonical" href="{SITE}/sortit/privacy/"><meta http-equiv="refresh" content="0; url=../"><a href="../">Privacy Policy</a>
""")
    support()
    get_page()
    beta_page()
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
