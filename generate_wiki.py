#!/usr/bin/env python3
"""
Generate Quartz wiki pages for all Likkutei Sichos.
Creates:
- Individual sicha pages (1,191 files)
- Volume index pages (39 volumes)
- Parsha/topic index pages
- Main index
"""
import os, re, json
from pathlib import Path
from collections import defaultdict, Counter

SRC = Path('/workspace/group/likkutei-sichos')
OUT = Path('/workspace/group/likkutei-sichos-wiki/content')
OUT.mkdir(parents=True, exist_ok=True)

# ── Hebrew parsha → English slug mapping ────────────────────────────────────
PARSHA_SLUGS = {
    'בראשית': 'bereishit', 'נח': 'noach', 'לך_לך': 'lech-lecha', 'לך לך': 'lech-lecha',
    'וירא': 'vayera', 'חיי_שרה': 'chayei-sarah', 'חיי שרה': 'chayei-sarah',
    'תולדות': 'toldot', 'ויצא': 'vayetzei', 'וישלח': 'vayishlach',
    'וישב': 'vayeshev', 'מקץ': 'miketz', 'ויגש': 'vayigash', 'ויחי': 'vayechi',
    'שמות': 'shemot', 'וארא': 'vaera', 'בא': 'bo', 'בשלח': 'beshalach',
    'יתרו': 'yitro', 'משפטים': 'mishpatim', 'תרומה': 'terumah', 'תצוה': 'tetzaveh',
    'תשא': 'ki-tisa', 'ויקהל': 'vayakhel', 'פקודי': 'pekudei',
    'ויקרא': 'vayikra', 'צו': 'tzav', 'שמיני': 'shemini',
    'תזריע': 'tazria', 'מצורע': 'metzora', 'אחרי': 'acharei', 'קדושים': 'kedoshim',
    'אמור': 'emor', 'בהר': 'behar', 'בחוקותי': 'bechukotai',
    'במדבר': 'bamidbar', 'נשא': 'naso', 'בהעלותך': 'behaalotecha',
    'שלח': 'shelach', 'קורח': 'korach', 'קרח': 'korach', 'חוקת': 'chukat',
    'בלק': 'balak', 'פנחס': 'pinchas', 'מטות': 'matot', 'מסעי': 'masei',
    'דברים': 'devarim', 'ואתחנן': 'vaetchanan', 'עקב': 'eikev', 'ראה': 'reeh',
    'שופטים': 'shoftim', 'תצא': 'ki-tetzei', 'תבוא': 'ki-tavo', 'תבא': 'ki-tavo',
    'נצבים': 'nitzavim', 'וילך': 'vayelech', 'האזינו': 'haazinu', 'ברכה': 'vezot-habracha',
    'וזאת_הברכה': 'vezot-habracha', 'וזאת הברכה': 'vezot-habracha',
    # Special days / holidays
    'חנוכה': 'chanukah', 'פורים': 'purim', 'פסח': 'pesach',
    'שבועות': 'shavuot', 'ראש_השנה': 'rosh-hashana', 'ראש השנה': 'rosh-hashana',
    'יום_כיפור': 'yom-kippur', 'סוכות': 'sukkot', 'שמחת_תורה': 'simchat-torah',
    'שמח_ת': 'simchat-torah', 'שמע_צ': 'shemini-atzeret',
    'י_ט_כסלו': 'yud-tes-kislev', 'יו_ד_שבט': 'yud-shvat', 'יו_ד_שבט': 'yud-shvat',
    'ל_ג_בעומר': 'lag-baomer', 'ט_ו_בשבט': 'tu-bishvat',
    'ט_ו_באב': 'tu-beav', 'י_ב_סיון': 'yud-beis-sivan',
    'ח_י_אלול': 'chai-elul', 'כ_ד_טבת': 'chof-dales-tevet',
    # abbreviated forms seen in filenames
    'חה_פ': 'pesach', 'חה_ש': 'shavuot', 'חה_ס': 'sukkot',
    'ר_ה': 'rosh-hashana', 'ש_ת': 'simchat-torah',
    'מטו_מ': 'matot-masei',
    'שבת_הגדול': 'shabbat-hagadol', 'שבת_חזון': 'shabbat-chazon',
    'פ\'_זכור': 'parshat-zachor', 'פ_זכור': 'parshat-zachor',
    'זכור': 'parshat-zachor',
    'ש_פ': 'shabbat-parshat',
    'שש_פ': 'shabbat-parshat-special',
}

HEBREW_PARTS = {'א': '1', 'ב': '2', 'ג': '3', 'ד': '4', 'ה': '5',
                'ו': '6', 'ז': '7', 'ח': '8', 'ט': '9', 'י': '10'}

def parse_filename(fname):
    """
    Parse filenames like:
    p0001_בראשית.txt → {page:1, topic_he:'בראשית', part_letter:'א', part_num:'1'}
    p0014_ואתחנן_א.txt → {page:14, topic_he:'ואתחנן', part_letter:'א', part_num:'1'}
    p0022_ואתחנן_ב.txt → {page:22, topic_he:'ואתחנן', part_letter:'ב', part_num:'2'}
    p0068_וישלח_-_י_ט_כסלו.txt → {page:68, topic_he:'וישלח_-_י_ט_כסלו', ...}
    """
    name = fname.replace('.txt', '')
    m = re.match(r'p(\d+)_(.*)', name)
    if not m:
        return None
    page = int(m.group(1))
    rest = m.group(2)

    # Check if ends with a single Hebrew letter part indicator
    # Pattern: ..._{letter} where letter is a single alef-beit letter
    parts = rest.split('_')
    if parts and len(parts[-1]) == 1 and parts[-1] in HEBREW_PARTS:
        topic_parts = parts[:-1]
        part_letter = parts[-1]
        part_num = HEBREW_PARTS[part_letter]
        topic_he = '_'.join(topic_parts)
    else:
        topic_he = rest
        part_letter = 'א'
        part_num = '1'

    return {'page': page, 'topic_he': topic_he, 'part_letter': part_letter, 'part_num': part_num}

def topic_slug(topic_he):
    """Convert Hebrew topic name to URL slug"""
    # Direct match
    if topic_he in PARSHA_SLUGS:
        return PARSHA_SLUGS[topic_he]
    # Clean spaces
    clean = topic_he.replace('_', ' ').strip()
    if clean in PARSHA_SLUGS:
        return PARSHA_SLUGS[clean]

    # Handle compound names like "וישלח_-_י_ט_כסלו" (parsha - holiday)
    # Split on " - " separator
    if '_-_' in topic_he:
        main, *rest = topic_he.split('_-_')
        main_slug = PARSHA_SLUGS.get(main, '')
        rest_he = '_'.join(rest)
        rest_slug = PARSHA_SLUGS.get(rest_he, '')
        if main_slug and rest_slug:
            return f"{main_slug}--{rest_slug}"
        elif main_slug:
            return main_slug + '--' + re.sub(r'[^\w]', '-', rest_he)[:20].strip('-')
        elif rest_slug:
            return rest_slug

    # Handle "שמע_צ-שמח_ת" style (joined with hyphen)
    if '-' in topic_he:
        first = topic_he.split('-')[0]
        if first in PARSHA_SLUGS:
            return PARSHA_SLUGS[first] + '-special'

    # Try first word
    first = parts[0] if (parts := topic_he.split('_')) else topic_he
    if first in PARSHA_SLUGS:
        suffix = re.sub(r'[^\w]', '-', topic_he.replace(first, '', 1).strip('_-'))[:20]
        return PARSHA_SLUGS[first] + ('-' + suffix if suffix else '')

    # Fallback: use raw topic
    slug = topic_he.replace('_', '-').replace(' ', '-').replace("'", '')
    slug = re.sub(r'[^\w\-]', '', slug)
    return slug.strip('-') or 'misc'

def safe_slug(s):
    """Make a filesystem-safe slug from any string."""
    s = s.replace('/', '-').replace('\\', '-')
    s = re.sub(r'[^\w\-]', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-') or 'page'

def get_first_paragraph(text, max_chars=600):
    """Extract opening paragraph for summary."""
    lines = text.strip().split('\n')
    body_lines = [l for l in lines if l.strip() and not l.startswith('#')]
    if not body_lines:
        return ''
    para = body_lines[0]
    if len(para) > max_chars:
        para = para[:max_chars] + '...'
    return para

def vol_num(vol_dir):
    return int(re.search(r'\d+', vol_dir).group())

# ── Collect all sichos ───────────────────────────────────────────────────────
all_sichos = []

for vol_dir in sorted(d for d in os.listdir(SRC) if d.startswith('volume_')):
    vol_n = vol_num(vol_dir)
    vol_path = SRC / vol_dir
    for fname in sorted(os.listdir(vol_path)):
        if not fname.endswith('.txt'):
            continue
        meta = parse_filename(fname)
        if not meta:
            continue
        text = (vol_path / fname).read_text(encoding='utf-8')
        slug = topic_slug(meta['topic_he'])
        # Ensure unique page_slug per (vol, file) by combining slug + part
        page_slug = safe_slug(f"{slug}_{meta['part_num']}")
        sicha = {
            'vol': vol_n,
            'vol_dir': vol_dir,
            'fname': fname,
            'page': meta['page'],
            'topic_he': meta['topic_he'],
            'part_letter': meta['part_letter'],
            'part_num': meta['part_num'],
            'slug': slug,
            'page_slug': page_slug,
            'text': text,
            'summary': get_first_paragraph(text),
        }
        all_sichos.append(sicha)

print(f"Collected {len(all_sichos)} sichos")

# ── Detect and fix duplicate page_slugs within same volume ──────────────────
# Track (vol, page_slug) collisions and deduplicate
seen = {}
for s in all_sichos:
    key = (s['vol'], s['page_slug'])
    if key in seen:
        # Disambiguate using page number
        s['page_slug'] = safe_slug(f"{s['slug']}_{s['page']}")
        seen[(s['vol'], s['page_slug'])] = s
    else:
        seen[key] = s

print(f"After dedup: {len(all_sichos)} sichos")

# ── Generate individual sicha pages ─────────────────────────────────────────
(OUT / 'sichos').mkdir(exist_ok=True)

for s in all_sichos:
    vol_slug = f"vol{s['vol']:02d}"
    (OUT / 'sichos' / vol_slug).mkdir(exist_ok=True)

    out_path = OUT / 'sichos' / vol_slug / f"{s['page_slug']}.md"

    dach_link = f"https://dach.dev/book/likkutei-sichos/viewer/{s['page']}_{s['vol']}"
    topic_display = s['topic_he'].replace('_', ' ').replace(' - ', ' — ')

    # Clean up title — remove internal quotes that break YAML
    title_clean = topic_display.replace('"', "'")

    content = f"""---
title: "{title_clean} · כרך {s['vol']} · {s['part_letter']}"
tags:
  - volume-{s['vol']}
  - {s['slug'].split('-')[0]}
  - likkutei-sichos
---

# {topic_display} · {s['part_letter']}

> **כרך:** [[volumes/volume-{s['vol']:02d}|כרך {s['vol']}]] · **פרשה/נושא:** [[topics/{s['slug']}|{topic_display}]] · **עמ':** {s['page']}

[Browse on dach.dev]({dach_link})

---

{s['text']}

---

*[[volumes/volume-{s['vol']:02d}|← כל שיחות כרך {s['vol']}]] · [[topics/{s['slug']}|← כל שיחות {topic_display}]]*
"""
    out_path.write_text(content, encoding='utf-8')

print(f"Generated sicha pages in content/sichos/")

# ── Generate volume index pages ──────────────────────────────────────────────
(OUT / 'volumes').mkdir(exist_ok=True)
by_vol = defaultdict(list)
for s in all_sichos:
    by_vol[s['vol']].append(s)

for vol_n, sichos in sorted(by_vol.items()):
    vol_slug = f"volume-{vol_n:02d}"
    rows = []
    for s in sorted(sichos, key=lambda x: x['page']):
        topic_display = s['topic_he'].replace('_', ' ').replace(' - ', ' — ')
        dach_link = f"https://dach.dev/book/likkutei-sichos/viewer/{s['page']}_{vol_n}"
        summary_short = s['summary'][:120].replace('|', '—') + ('...' if len(s['summary']) > 120 else '')
        rows.append(f"| [[sichos/vol{vol_n:02d}/{s['page_slug']}\\|{topic_display} {s['part_letter']}]] | {s['page']} | [dach.dev]({dach_link}) | {summary_short} |")

    table = "| שיחה | עמ' | מקור | תוכן |\n|------|-----|------|------|\n" + '\n'.join(rows)

    content = f"""---
title: "ליקוטי שיחות — כרך {vol_n}"
tags:
  - volume-{vol_n}
  - likkutei-sichos
---

# ליקוטי שיחות — כרך {vol_n}

**{len(sichos)} שיחות** · [Browse volume on dach.dev](https://dach.dev/book/likkutei-sichos/toc?volume={vol_n})

## רשימת השיחות

{table}

---

*[[index|← חזרה לדף הראשי]]*
"""
    (OUT / 'volumes' / f"{vol_slug}.md").write_text(content, encoding='utf-8')

print(f"Generated {len(by_vol)} volume pages")

# ── Generate parsha/topic index pages ───────────────────────────────────────
(OUT / 'topics').mkdir(exist_ok=True)
by_topic = defaultdict(list)
for s in all_sichos:
    by_topic[s['slug']].append(s)

for slug, sichos in sorted(by_topic.items()):
    topic_he = Counter(s['topic_he'] for s in sichos).most_common(1)[0][0]
    topic_display = topic_he.replace('_', ' ').replace(' - ', ' — ')
    title_clean = topic_display.replace('"', "'")

    rows = []
    for s in sorted(sichos, key=lambda x: (x['vol'], x['page'])):
        summary_short = s['summary'][:120].replace('|', '—') + ('...' if len(s['summary']) > 120 else '')
        rows.append(f"| [[volumes/volume-{s['vol']:02d}\\|כרך {s['vol']}]] | [[sichos/vol{s['vol']:02d}/{s['page_slug']}\\|{s['part_letter']}]] | {s['page']} | {summary_short} |")

    table = "| כרך | חלק | עמ' | תוכן |\n|-----|-----|-----|------|\n" + '\n'.join(rows)

    content = f"""---
title: "{title_clean} — ליקוטי שיחות"
tags:
  - {slug.split('-')[0]}
  - likkutei-sichos
---

# {topic_display}

**{len(sichos)} שיחות** בכל הכרכים

## כל השיחות על {topic_display}

{table}

---

*[[index|← חזרה לדף הראשי]] · [[volumes/index|כרכים]]*
"""
    (OUT / 'topics' / f"{slug}.md").write_text(content, encoding='utf-8')

print(f"Generated {len(by_topic)} topic pages")

# ── Generate volumes index ────────────────────────────────────────────────────
vol_rows = []
for vol_n in sorted(by_vol.keys()):
    count = len(by_vol[vol_n])
    vol_rows.append(f"| [[volumes/volume-{vol_n:02d}\\|כרך {vol_n}]] | {count} | [dach.dev](https://dach.dev/book/likkutei-sichos/toc?volume={vol_n}) |")

vol_table = "| כרך | שיחות | מקור |\n|-----|-------|------|\n" + '\n'.join(vol_rows)

(OUT / 'volumes' / 'index.md').write_text(f"""---
title: "כל הכרכים — ליקוטי שיחות"
tags: [likkutei-sichos, volumes]
---

# כל הכרכים

{vol_table}
""", encoding='utf-8')

# ── Generate topics index ─────────────────────────────────────────────────────
topic_rows = []
for slug, sichos in sorted(by_topic.items(), key=lambda x: -len(x[1])):
    topic_he = Counter(s['topic_he'] for s in sichos).most_common(1)[0][0]
    topic_display = topic_he.replace('_', ' ').replace(' - ', ' — ')
    topic_rows.append(f"| [[topics/{slug}\\|{topic_display}]] | {len(sichos)} |")

topic_table = "| נושא/פרשה | שיחות |\n|-----------|-------|\n" + '\n'.join(topic_rows)

(OUT / 'topics' / 'index.md').write_text(f"""---
title: "כל הנושאים — ליקוטי שיחות"
tags: [likkutei-sichos, topics]
---

# כל הנושאים והפרשיות

{topic_table}
""", encoding='utf-8')

# ── Generate main index ───────────────────────────────────────────────────────
total_vols = len(by_vol)
total_topics = len(by_topic)
total_sichos = len(all_sichos)

SEFER_GROUPS = {
    'בראשית': ['bereishit','noach','lech-lecha','vayera','chayei-sarah','toldot','vayetzei','vayishlach','vayeshev','miketz','vayigash','vayechi'],
    'שמות': ['shemot','vaera','bo','beshalach','yitro','mishpatim','terumah','tetzaveh','ki-tisa','vayakhel','pekudei'],
    'ויקרא': ['vayikra','tzav','shemini','tazria','metzora','acharei','kedoshim','emor','behar','bechukotai'],
    'במדבר': ['bamidbar','naso','behaalotecha','shelach','korach','chukat','balak','pinchas','matot','masei'],
    'דברים': ['devarim','vaetchanan','eikev','reeh','shoftim','ki-tetzei','ki-tavo','nitzavim','vayelech','haazinu','vezot-habracha'],
}

sefer_sections = []
for sefer_he, parsha_slugs_list in SEFER_GROUPS.items():
    links = []
    for ps in parsha_slugs_list:
        if ps in by_topic:
            topic_he = Counter(s['topic_he'] for s in by_topic[ps]).most_common(1)[0][0]
            topic_display = topic_he.replace('_', ' ')
            count = len(by_topic[ps])
            links.append(f"[[topics/{ps}|{topic_display}]] ({count})")
    if links:
        sefer_sections.append(f"### {sefer_he}\n" + ' · '.join(links))

torah_nav = '\n\n'.join(sefer_sections)

# Holidays section - collect all holiday slugs
holiday_slugs = ['chanukah', 'purim', 'pesach', 'shavuot', 'sukkot', 'rosh-hashana',
                 'simchat-torah', 'yud-tes-kislev', 'yud-shvat', 'lag-baomer',
                 'tu-bishvat', 'chai-elul', 'chof-dales-tevet']
holiday_links = []
for s in holiday_slugs:
    if s in by_topic:
        topic_he = Counter(si['topic_he'] for si in by_topic[s]).most_common(1)[0][0]
        topic_display = topic_he.replace('_', ' ')
        holiday_links.append(f"[[topics/{s}|{topic_display}]] ({len(by_topic[s])})")

holiday_section = ' · '.join(holiday_links)

vol_links = ' · '.join(f"[[volumes/volume-{n:02d}|כרך {n}]]" for n in sorted(by_vol.keys()))

index_content = f"""---
title: "ליקוטי שיחות — אוצר השיחות"
tags: [likkutei-sichos, index]
---

# ליקוטי שיחות — אוצר השיחות

> **{total_sichos:,} שיחות** · **{total_vols} כרכים** · **{total_topics} נושאים ופרשיות**
>
> ליקוטי שיחות הוא אוסף שיחות תורה של הרבי מליובאוויטש — הרבי מנחם מענדל שניאורסאהן — שנאמרו ברבים ועוּבְּדו לדפוס. הוא מכסה את כל פרשיות התורה, מועדים, וענינים חסידיים.

## ניווט

### [[volumes/index|כרכים]] · [[topics/index|נושאים]] · [dach.dev](https://dach.dev/book/likkutei-sichos)

---

## ניווט לפי פרשת השבוע

{torah_nav}

---

## ימים טובים ומועדים

{holiday_section}

---

## כל {total_vols} הכרכים

{vol_links}

---

*[Browse full corpus on dach.dev](https://dach.dev/book/likkutei-sichos)*
"""

(OUT / 'index.md').write_text(index_content, encoding='utf-8')
print("Generated main index")

# ── Save manifest ─────────────────────────────────────────────────────────────
manifest = {
    'total_sichos': total_sichos,
    'total_volumes': total_vols,
    'total_topics': total_topics,
    'volumes': {str(k): len(v) for k, v in by_vol.items()},
    'topics': {k: len(v) for k, v in by_topic.items()},
}
with open(OUT.parent / 'wiki_manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\nDONE!")
print(f"   Sicha pages: {total_sichos}")
print(f"   Volume pages: {total_vols}")
print(f"   Topic pages: {total_topics}")
print(f"   Total content pages: {total_sichos + total_vols + total_topics + 4}")
