#!/usr/bin/env python3
"""
Generate comprehensive parsha + yomim tovim pages for Likkutei Sichos wiki.
Covers ALL Torah parshas + ALL yomim tovim (including Chassidishe).
"""
import os, re, json
from pathlib import Path
from collections import defaultdict, Counter

OUT = Path('/workspace/group/likkutei-sichos-wiki/content')
SRC = Path('/workspace/group/likkutei-sichos')

with open('/workspace/group/likkutei-sichos-wiki/wiki_manifest.json') as f:
    manifest = json.load(f)
existing_topics = manifest['topics']  # slug → count

# ── COMPLETE Torah parsha list ───────────────────────────────────────────────
# Format: (hebrew_name, english_name, slug, sefer, parsha_number)
ALL_PARSHAS = [
    # Bereishit
    ('בראשית', 'Bereishit', 'bereishit', 'בראשית', 1),
    ('נח', 'Noach', 'noach', 'בראשית', 2),
    ('לך לך', 'Lech Lecha', 'lech-lecha', 'בראשית', 3),
    ('וירא', 'Vayera', 'vayera', 'בראשית', 4),
    ('חיי שרה', 'Chayei Sarah', 'chayei-sarah', 'בראשית', 5),
    ('תולדות', 'Toldot', 'toldot', 'בראשית', 6),
    ('ויצא', 'Vayetzei', 'vayetzei', 'בראשית', 7),
    ('וישלח', 'Vayishlach', 'vayishlach', 'בראשית', 8),
    ('וישב', 'Vayeshev', 'vayeshev', 'בראשית', 9),
    ('מקץ', 'Miketz', 'miketz', 'בראשית', 10),
    ('ויגש', 'Vayigash', 'vayigash', 'בראשית', 11),
    ('ויחי', 'Vayechi', 'vayechi', 'בראשית', 12),
    # Shemot
    ('שמות', 'Shemot', 'shemot', 'שמות', 13),
    ('וארא', "Va'era", 'vaera', 'שמות', 14),
    ('בא', 'Bo', 'bo', 'שמות', 15),
    ('בשלח', 'Beshalach', 'beshalach', 'שמות', 16),
    ('יתרו', 'Yitro', 'yitro', 'שמות', 17),
    ('משפטים', 'Mishpatim', 'mishpatim', 'שמות', 18),
    ('תרומה', 'Terumah', 'terumah', 'שמות', 19),
    ('תצוה', 'Tetzaveh', 'tetzaveh', 'שמות', 20),
    ('כי תשא', 'Ki Tisa', 'ki-tisa', 'שמות', 21),
    ('ויקהל', 'Vayakhel', 'vayakhel', 'שמות', 22),
    ('פקודי', 'Pekudei', 'pekudei', 'שמות', 23),
    # Vayikra
    ('ויקרא', 'Vayikra', 'vayikra', 'ויקרא', 24),
    ('צו', 'Tzav', 'tzav', 'ויקרא', 25),
    ('שמיני', 'Shemini', 'shemini', 'ויקרא', 26),
    ('תזריע', 'Tazria', 'tazria', 'ויקרא', 27),
    ('מצורע', 'Metzora', 'metzora', 'ויקרא', 28),
    ('אחרי מות', 'Acharei Mot', 'acharei', 'ויקרא', 29),
    ('קדושים', 'Kedoshim', 'kedoshim', 'ויקרא', 30),
    ('אמור', 'Emor', 'emor', 'ויקרא', 31),
    ('בהר', 'Behar', 'behar', 'ויקרא', 32),
    ('בחוקותי', 'Bechukotai', 'bechukotai', 'ויקרא', 33),
    # Bamidbar
    ('במדבר', 'Bamidbar', 'bamidbar', 'במדבר', 34),
    ('נשא', 'Naso', 'naso', 'במדבר', 35),
    ('בהעלותך', "Behaalotecha", 'behaalotecha', 'במדבר', 36),
    ('שלח', 'Shelach', 'shelach', 'במדבר', 37),
    ('קרח', 'Korach', 'korach', 'במדבר', 38),
    ('חוקת', 'Chukat', 'chukat', 'במדבר', 39),
    ('בלק', 'Balak', 'balak', 'במדבר', 40),
    ('פינחס', 'Pinchas', 'pinchas', 'במדבר', 41),
    ('מטות', 'Matot', 'matot', 'במדבר', 42),
    ('מסעי', 'Masei', 'masei', 'במדבר', 43),
    # Devarim
    ('דברים', 'Devarim', 'devarim', 'דברים', 44),
    ('ואתחנן', "Va'etchanan", 'vaetchanan', 'דברים', 45),
    ('עקב', 'Eikev', 'eikev', 'דברים', 46),
    ('ראה', 'Reeh', 'reeh', 'דברים', 47),
    ('שופטים', 'Shoftim', 'shoftim', 'דברים', 48),
    ('כי תצא', 'Ki Tetzei', 'ki-tetzei', 'דברים', 49),
    ('כי תבוא', 'Ki Tavo', 'ki-tavo', 'דברים', 50),
    ('נצבים', 'Nitzavim', 'nitzavim', 'דברים', 51),
    ('וילך', 'Vayelech', 'vayelech', 'דברים', 52),
    ('האזינו', "Ha'azinu", 'haazinu', 'דברים', 53),
    ('וזאת הברכה', "Vezot Habracha", 'vezot-habracha', 'דברים', 54),
]

# ── COMPLETE Yomim Tovim list ────────────────────────────────────────────────
# (hebrew, english, slug, category, date_he, description)
ALL_YOMIM_TOVIM = [
    # ── Shalosh Regalim ─────────────────────────────────────────────────────
    ('פסח', 'Pesach', 'pesach', 'שלש רגלים', 'ט"ו ניסן', 'חג הפסח — זמן חירותנו'),
    ('שבועות', 'Shavuot', 'shavuot', 'שלש רגלים', "ו' סיון", 'חג השבועות — זמן מתן תורתנו'),
    ('סוכות', 'Sukkot', 'sukkot', 'שלש רגלים', 'ט"ו תשרי', 'חג הסוכות — זמן שמחתנו'),
    ('שמיני עצרת ושמחת תורה', 'Shemini Atzeret / Simchat Torah', 'shemini-atzeret', 'שלש רגלים', 'כ"ב תשרי', 'שמיני עצרת ושמחת תורה'),
    # ── ימים נוראים ─────────────────────────────────────────────────────────
    ('ראש השנה', 'Rosh Hashana', 'rosh-hashana', 'ימים נוראים', "א' תשרי", 'ראש השנה — יום הדין'),
    ('יום כיפור', 'Yom Kippur', 'yom-kippur', 'ימים נוראים', "י' תשרי", 'יום הכיפורים — יום הסליחה'),
    # ── ימים טובים נוספים ───────────────────────────────────────────────────
    ('חנוכה', 'Chanukah', 'chanukah', 'ימים טובים', 'כ"ה כסלו', 'חנוכה — חג האורים'),
    ('פורים', 'Purim', 'purim', 'ימים טובים', 'י"ד אדר', 'פורים — זמן שמחתנו'),
    ('ט"ו בשבט', "Tu B'Shvat", 'tu-bishvat', 'ימים טובים', 'ט"ו שבט', 'ראש השנה לאילנות'),
    ('ל"ג בעומר', "Lag BaOmer", 'lag-baomer', 'ימים טובים', 'י"ח אייר', 'הילולת רשב"י — ל"ג בעומר'),
    ('ט"ו באב', "Tu BeAv", 'tu-beav', 'ימים טובים', 'ט"ו אב', 'יום האהבה — ט"ו באב'),
    # ── צומות ──────────────────────────────────────────────────────────────
    ('עשרה בטבת', 'Asara BeTevet', 'asara-betevet', 'צומות', "י' טבת", 'צום עשרה בטבת'),
    ('תענית אסתר', "Ta'anit Esther", 'taanit-esther', 'צומות', 'י"ג אדר', 'תענית אסתר'),
    ('שבעה עשר בתמוז', "Shiva Asar BeTammuz", 'shiva-asar-betammuz', 'צומות', 'י"ז תמוז', 'צום י"ז בתמוז'),
    ('תשעה באב', "Tisha BeAv", 'tisha-beav', 'צומות', "ט' אב", 'תשעה באב — צום החורבן'),
    # ── שבתות מיוחדות ───────────────────────────────────────────────────────
    ('שבת שובה', 'Shabbat Shuva', 'shabbat-shuva', 'שבתות מיוחדות', 'שבת שבין ר"ה לי"כ', 'שבת שובה — שבת התשובה'),
    ('שבת הגדול', 'Shabbat HaGadol', 'shabbat-hagadol', 'שבתות מיוחדות', 'שבת לפני פסח', 'שבת הגדול'),
    ('שבת חזון', 'Shabbat Chazon', 'shabbat-chazon', 'שבתות מיוחדות', 'שבת לפני ט"ב', 'שבת חזון'),
    ('שבת נחמו', 'Shabbat Nachamu', 'shabbat-nachamu', 'שבתות מיוחדות', 'שבת אחרי ט"ב', 'שבת נחמו'),
    ('שבת בראשית', 'Shabbat Bereishit', 'shabbat-bereishit', 'שבתות מיוחדות', 'ראשונה אחרי שמח"ת', 'שבת בראשית'),
    # ── ד' פרשיות ─────────────────────────────────────────────────────────
    ('פרשת שקלים', "Parshat Shekalim", 'parshat-shekalim', "ד' פרשיות", 'ניסן/אדר', "פ' שקלים"),
    ('פרשת זכור', "Parshat Zachor", 'parshat-zachor', "ד' פרשיות", 'לפני פורים', "פ' זכור"),
    ('פרשת פרה', "Parshat Parah", 'parshat-parah', "ד' פרשיות", 'ניסן', "פ' פרה"),
    ('פרשת החודש', "Parshat HaChodesh", 'parshat-hachodesh', "ד' פרשיות", 'ניסן', "פ' החודש"),
    # ── ימים טובים חסידיים ──────────────────────────────────────────────────
    ('י"ט כסלו', "Yud-Tes Kislev", 'yud-tes-kislev', 'ימים טובים חסידיים', 'י"ט כסלו', 'ראש השנה לחסידות — גאולת אדמו"ר הזקן תקנ"ח'),
    ("י' שבט", "Yud Shvat", 'yud-shvat', 'ימים טובים חסידיים', "י' שבט", 'יארצייט הרייאצ"ה — קבלת נשיאות הרבי תשי"א'),
    ('י"א ניסן', "Yud-Alef Nissan", 'yud-alef-nissan', 'ימים טובים חסידיים', 'י"א ניסן', 'יום הולדת הרבי'),
    ("ג' תמוז", "Gimmel Tammuz", 'gimmel-tammuz', 'ימים טובים חסידיים', "ג' תמוז", 'גימ"ל תמוז תשנ"ד'),
    ('י"ב-י"ג תמוז', "Yud-Beis Tammuz", 'yud-beis-tammuz', 'ימים טובים חסידיים', 'י"ב תמוז', 'גאולת הרייאצ"ה תרפ"ז'),
    ('י"ב סיון', "Yud-Beis Sivan", 'yud-beis-sivan', 'ימים טובים חסידיים', 'י"ב סיון', 'חג הגאולה הרייאצ"ה'),
    ('ח"י אלול', "Chai Elul", 'chai-elul', 'ימים טובים חסידיים', 'י"ח אלול', 'יום הולדת הבעש"ט ואדמו"ר הזקן — ח"י אלול'),
    ('כ"ד טבת', "Chof-Dalet Tevet", 'chof-dalet-tevet', 'ימים טובים חסידיים', 'כ"ד טבת', 'יארצייט אדמו"ר הזקן בעל התניא'),
    ("ב' ניסן", "Beis Nissan", 'beis-nissan', 'ימים טובים חסידיים', "ב' ניסן", 'יארצייט אדמו"ר הזקן — צמח צדק'),
    ("כ' אב", "Chof Av", 'chof-av', 'ימים טובים חסידיים', "כ' אב", 'יארצייט הרב לוי יצחק שניאורסאהן'),
    ("ז' אדר", "Zayin Adar", 'zayin-adar', 'ימים טובים חסידיים', "ז' אדר", 'יום הולדת ויארצייט משה רבינו'),
    ("כ' מר חשוון", "Chof MarCheshvan", 'chof-marcheshvan', 'ימים טובים חסידיים', "כ' חשוון", 'יום הולדת הרמב"ם ויום הסתלקות מהר"ש'),
    ("ב' סיון", "Beis Sivan", 'beis-sivan', 'ימים טובים חסידיים', "ב' סיון", 'יום מתן תורה — מגביל'),
    ("ט' כסלו", "Tes Kislev", 'tes-kislev', 'ימים טובים חסידיים', "ט' כסלו", 'יום הולדת ויארצייט האמצעי — מיטעלר רבי'),
    ("י' כסלו", "Yud Kislev", 'yud-kislev', 'ימים טובים חסידיים', "י' כסלו", 'גאולת האמצעי'),
    ('י"ד כסלו', "Yud-Dalet Kislev", 'yud-dalet-kislev', 'ימים טובים חסידיים', 'י"ד כסלו', 'יום חתונת הרבי'),
    ("ר\"ח חשוון", "Rosh Chodesh Cheshvan", 'rosh-chodesh-cheshvan', 'ראשי חדשים', "א' חשוון", 'ראש חודש חשוון'),
    ("ר\"ח כסלו", "Rosh Chodesh Kislev", 'rosh-chodesh-kislev', 'ראשי חדשים', "א' כסלו", 'ראש חודש כסלו'),
    ("ר\"ח ניסן", "Rosh Chodesh Nissan", 'rosh-chodesh-nissan', 'ראשי חדשים', "א' ניסן", 'ראש חודש ניסן'),
    ("ר\"ח סיון", "Rosh Chodesh Sivan", 'rosh-chodesh-sivan', 'ראשי חדשים', "א' סיון", 'ראש חודש סיון'),
    ("ר\"ח שבט", "Rosh Chodesh Shvat", 'rosh-chodesh-shvat', 'ראשי חדשים', "א' שבט", 'ראש חודש שבט'),
]

# Use existing manifest
topics_data = manifest['topics']  # slug → count of sichos

# ── Generate comprehensive parsha pages ─────────────────────────────────────
(OUT / 'parshiyot').mkdir(exist_ok=True)

SEFER_DESCRIPTIONS = {
    'בראשית': 'ספר בראשית — מעשה בראשית, אבות האומה, ירידת יעקב למצרים',
    'שמות': 'ספר שמות — גלות וגאולת מצרים, מתן תורה, המשכן',
    'ויקרא': 'ספר ויקרא — קרבנות, קדושה, מועדים',
    'במדבר': 'ספר במדבר — מסעות במדבר, חטאים ותיקונם',
    'דברים': 'ספר דברים — משנה תורה, דברי משה לפני פטירתו',
}

for he_name, en_name, slug, sefer, parsha_num in ALL_PARSHAS:
    # Get actual sichos count for this parsha
    count = topics_data.get(slug, 0)

    # Get sicha table from existing topic page if it exists
    topic_page = OUT / 'topics' / f'{slug}.md'
    sicha_table_section = ''
    if topic_page.exists():
        existing = topic_page.read_text(encoding='utf-8')
        # Extract everything after the first table
        table_match = re.search(r'\| כרך.*', existing, re.DOTALL)
        if table_match:
            sicha_table_section = table_match.group(0)

    # Find adjacent parshas for navigation
    idx = next((i for i,p in enumerate(ALL_PARSHAS) if p[2]==slug), None)
    prev_link = f"[[parshiyot/{ALL_PARSHAS[idx-1][2]}|← {ALL_PARSHAS[idx-1][0]}]]" if idx and idx > 0 else ''
    next_link = f"[[parshiyot/{ALL_PARSHAS[idx+1][2]}|{ALL_PARSHAS[idx+1][0]} →]]" if idx is not None and idx < len(ALL_PARSHAS)-1 else ''

    # Also check for related slugs (e.g. 'matot' and 'masei' might combine)
    related_slugs = []
    for t_slug in topics_data:
        if slug in t_slug and t_slug != slug:
            related_slugs.append(t_slug)

    related_section = ''
    if related_slugs:
        related_links = ', '.join(f"[[topics/{rs}|{rs}]]" for rs in related_slugs[:5])
        related_section = "\n## נושאים קשורים\n\n" + related_links + "\n"

    count_line = f"**{count} שיחות** בליקוטי שיחות" if count else "*(אין שיחות מפורטות בפרשה זו בקובץ)*"
    topic_link = f"[[topics/{slug}|→ לדף הנושא המלא עם כל השיחות]]" if count else ""
    sicha_section = f"## כל השיחות על פרשת {he_name}\n\n{sicha_table_section}" if sicha_table_section else ""
    sefer_tag = sefer.replace(' ', '-').lower()
    # Escape double-quotes in YAML title (Hebrew gershayim)
    yaml_he_name = he_name.replace('"', '\\"')

    content = f"""---
title: "פרשת {yaml_he_name} — ליקוטי שיחות"
tags:
  - parsha
  - {slug}
  - {sefer_tag}
  - likkutei-sichos
---

# פרשת {he_name}

> **{SEFER_DESCRIPTIONS.get(sefer, sefer)}** · פרשה {parsha_num} · {en_name}

{count_line}

{topic_link}

## ניווט

{prev_link} | [[index|ראשי]] | {next_link}
{related_section}
{sicha_section}
"""
    (OUT / 'parshiyot' / f'{slug}.md').write_text(content, encoding='utf-8')

print(f"Generated {len(ALL_PARSHAS)} parsha pages in content/parshiyot/")

# ── Generate sefer index pages ───────────────────────────────────────────────
(OUT / 'sfarim').mkdir(exist_ok=True)
sefarim_parshas = defaultdict(list)
for p in ALL_PARSHAS:
    sefarim_parshas[p[3]].append(p)

for sefer_he, parshas in sefarim_parshas.items():
    sefer_slug = {'בראשית': 'bereishit', 'שמות': 'shemot', 'ויקרא': 'vayikra',
                  'במדבר': 'bamidbar', 'דברים': 'devarim'}[sefer_he]
    rows = []
    total_in_sefer = 0
    for he, en, slug, sefer, num in parshas:
        cnt = topics_data.get(slug, 0)
        total_in_sefer += cnt
        cnt_str = str(cnt) if cnt else '—'
        rows.append(f"| {num} | [[parshiyot/{slug}\\|{he}]] | {en} | {cnt_str} |")

    table = "| # | פרשה | English | שיחות |\n|---|------|---------|-------|\n" + '\n'.join(rows)

    content = f"""---
title: "ספר {sefer_he} — ליקוטי שיחות"
tags:
  - sefer
  - {sefer_slug}
  - likkutei-sichos
---

# ספר {sefer_he}

> {SEFER_DESCRIPTIONS[sefer_he]}
>
> **{total_in_sefer} שיחות** בספר זה · **{len(parshas)} פרשיות**

{table}

---

*[[parshiyot/index|← כל הפרשיות]] · [[index|ראשי]]*
"""
    (OUT / 'sfarim' / f'{sefer_slug}.md').write_text(content, encoding='utf-8')

print(f"Generated 5 sefer pages")

# ── Generate parshiyot index ─────────────────────────────────────────────────
sefer_sections_all = []
for sefer_he, parshas in sefarim_parshas.items():
    sefer_slug = {'בראשית': 'bereishit', 'שמות': 'shemot', 'ויקרא': 'vayikra',
                  'במדבר': 'bamidbar', 'דברים': 'devarim'}[sefer_he]
    links = []
    for p in parshas:
        cnt = topics_data.get(p[2], 0)
        cnt_str = f" ({cnt})" if cnt else ""
        links.append(f"[[parshiyot/{p[2]}|{p[0]}]]{cnt_str}")
    sefer_sections_all.append(f"### [[sfarim/{sefer_slug}|ספר {sefer_he}]]\n\n" + ' · '.join(links))

(OUT / 'parshiyot' / 'index.md').write_text(f"""---
title: "כל הפרשיות — ליקוטי שיחות"
tags: [parshiyot, likkutei-sichos]
---

# כל פרשיות השבוע

{chr(10).join(sefer_sections_all)}

---

*[[index|ראשי]]*
""", encoding='utf-8')
print("Generated parshiyot index")

# ── Generate yomim tovim pages ───────────────────────────────────────────────
(OUT / 'yomim-tovim').mkdir(exist_ok=True)
yt_by_category = defaultdict(list)
for yt in ALL_YOMIM_TOVIM:
    yt_by_category[yt[3]].append(yt)

for he_name, en_name, slug, category, date_he, description in ALL_YOMIM_TOVIM:
    count = topics_data.get(slug, 0)

    # Get sicha table from existing topic page if it exists
    topic_page = OUT / 'topics' / f'{slug}.md'
    sicha_table_section = ''
    if topic_page.exists():
        existing = topic_page.read_text(encoding='utf-8')
        table_match = re.search(r'\| כרך.*', existing, re.DOTALL)
        if table_match:
            sicha_table_section = table_match.group(0)

    # Find related slugs
    related_slugs = [t for t in topics_data if slug in t and t != slug]
    related_section = ''
    if related_slugs:
        related_links = ', '.join(f"[[topics/{rs}|{rs}]]" for rs in related_slugs[:5])
        related_section = "\n## נושאים קשורים\n\n" + related_links + "\n"

    # Category context
    cat_descriptions = {
        'שלש רגלים': 'שלש רגלים — פסח, שבועות, סוכות',
        'ימים נוראים': 'ימים הנוראים — ראש השנה ויום הכיפורים',
        'ימים טובים': 'ימים טובים',
        'צומות': 'ימי צום',
        'שבתות מיוחדות': 'שבתות מיוחדות',
        "ד' פרשיות": 'ארבע פרשיות',
        'ימים טובים חסידיים': 'ימים טובים חסידיים — ימי גאולה ויארציייטן',
        'ראשי חדשים': 'ראשי חדשים',
    }

    # Safe tag from category
    safe_cat_tag = re.sub(r'[^\w-]', '-', category)

    yt_count_line = f"**{count} שיחות** בליקוטי שיחות" if count else "*(אין שיחות ספציפיות על יום זה בקובץ)*"
    yt_topic_link = f"[[topics/{slug}|→ לדף הנושא המלא עם כל השיחות]]" if count else ""
    yt_sicha_section = f"## כל השיחות על {he_name}\n\n{sicha_table_section}" if sicha_table_section else ""
    cat_desc = cat_descriptions.get(category, category)
    # Escape double-quotes in YAML title (Hebrew gershayim)
    yaml_yt_he_name = he_name.replace('"', '\\"')

    content = f"""---
title: "{yaml_yt_he_name} — ליקוטי שיחות"
tags:
  - yom-tov
  - {slug}
  - {safe_cat_tag}
  - likkutei-sichos
---

# {he_name}

> **{description}**
>
> תאריך: **{date_he}** · קטגוריה: {cat_desc}

{yt_count_line}

{yt_topic_link}
{related_section}
{yt_sicha_section}

---

*[[yomim-tovim/index|← כל ימי השנה]] · [[index|ראשי]]*
"""
    (OUT / 'yomim-tovim' / f'{slug}.md').write_text(content, encoding='utf-8')

# ── Generate yomim tovim index ───────────────────────────────────────────────
yt_sections = []
for cat, items in yt_by_category.items():
    links = []
    for he, en, sl, *_ in items:
        cnt = topics_data.get(sl, 0)
        cnt_str = f" ({cnt})" if cnt else ""
        links.append(f"[[yomim-tovim/{sl}|{he}]]{cnt_str}")
    yt_sections.append(f"### {cat}\n\n" + ' · '.join(links))

(OUT / 'yomim-tovim' / 'index.md').write_text(f"""---
title: "ימים טובים — ליקוטי שיחות"
tags: [yomim-tovim, likkutei-sichos]
---

# ימים טובים ומועדים

{chr(10).join(yt_sections)}

---

*[[index|ראשי]]*
""", encoding='utf-8')

print(f"Generated {len(ALL_YOMIM_TOVIM)} yom tov pages + index")

# ── Update main index to include new sections ────────────────────────────────
main_index = OUT / 'index.md'
existing_index = main_index.read_text(encoding='utf-8')

# Add parshiyot and yomim tovim nav links if not already there
if '[[parshiyot/index' not in existing_index:
    nav_addition = "\n### [[parshiyot/index|פרשיות השבוע]] · [[yomim-tovim/index|ימים טובים]] · [[sfarim/bereishit|חמשה חומשי תורה]]\n"
    existing_index = existing_index.replace(
        "### [[volumes/index|כרכים]]",
        f"### [[volumes/index|כרכים]]{nav_addition}"
    )
    main_index.write_text(existing_index, encoding='utf-8')
    print("Updated main index with new navigation")
else:
    print("Main index already has parshiyot navigation")

# ── Final count ──────────────────────────────────────────────────────────────
import subprocess
result = subprocess.run(['find', str(OUT), '-name', '*.md', '-not', '-path', '*/node_modules/*'],
                       capture_output=True, text=True)
total = len(result.stdout.strip().split('\n'))
print(f"\nTotal .md pages: {total}")
print(f"   Parsha pages: {len(ALL_PARSHAS)}")
print(f"   Yom tov pages: {len(ALL_YOMIM_TOVIM)}")
print(f"   Sefer pages: 5")
