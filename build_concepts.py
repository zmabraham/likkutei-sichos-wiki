#!/usr/bin/env python3
"""
Comprehensive concept article builder for Likkutei Sichos wiki.
Processes 98 concept files with rich excerpts from sicha content.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

WIKI_ROOT = Path("/workspace/group/likkutei-sichos-wiki")
SICHOS_DIR = WIKI_ROOT / "content" / "sichos"
CONCEPTS_DIR = WIKI_ROOT / "content" / "concepts"

# ============================================================
# STEP 1: Load all sicha files into memory
# ============================================================

print("Loading all sicha files...")

# sicha_data: list of dicts with keys: vol, slug, title, page, content, path
sicha_data = []

for vol_dir in sorted(SICHOS_DIR.iterdir()):
    if not vol_dir.is_dir():
        continue
    vol_num = int(vol_dir.name.replace("vol", ""))
    for sicha_file in sorted(vol_dir.glob("*.md")):
        content = sicha_file.read_text(encoding="utf-8")
        # Extract page number from frontmatter/header
        page_match = re.search(r"עמ'[:\s]+(\d+)", content)
        page = int(page_match.group(1)) if page_match else 0
        # Extract title from frontmatter
        title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        title = title_match.group(1).strip('"\'') if title_match else sicha_file.stem
        # Strip frontmatter for searching
        body = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
        slug = sicha_file.stem
        sicha_data.append({
            "vol": vol_num,
            "slug": slug,
            "title": title,
            "page": page,
            "content": body,
            "lines": body.split('\n'),
            "vol_str": f"vol{vol_num:02d}",
        })

print(f"Loaded {len(sicha_data)} sicha files.")

# ============================================================
# STEP 2: Helper to extract excerpt around a match
# ============================================================

def extract_excerpt(lines, match_line_idx, max_chars=150):
    """Extract 2-3 lines of context around a match, strip markdown."""
    start = max(0, match_line_idx)
    # Collect lines until we have enough text
    excerpt_lines = []
    for i in range(start, min(start + 4, len(lines))):
        line = lines[i].strip()
        if line and not line.startswith('#') and not line.startswith('|') and not line.startswith('>'):
            excerpt_lines.append(line)
        if len(' '.join(excerpt_lines)) > max_chars:
            break
    text = ' '.join(excerpt_lines)
    # Clean up
    text = re.sub(r'\[\[.*?\|([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0] + '...'
    return text

def find_matches(patterns, sicha_data, max_results=50):
    """
    Find all sicha files matching any of the patterns.
    Returns list of (vol, slug, title, page, excerpt) sorted by vol then page.
    Deduplicates by (vol, slug).
    """
    results = {}
    for sicha in sicha_data:
        key = (sicha["vol"], sicha["slug"])
        if key in results:
            continue
        for pat in patterns:
            for i, line in enumerate(sicha["lines"]):
                if re.search(pat, line):
                    excerpt = extract_excerpt(sicha["lines"], i)
                    results[key] = {
                        "vol": sicha["vol"],
                        "slug": sicha["slug"],
                        "title": sicha["title"],
                        "page": sicha["page"],
                        "excerpt": excerpt,
                    }
                    break
            if key in results:
                break
    # Sort by vol, then page
    sorted_results = sorted(results.values(), key=lambda x: (x["vol"], x["page"]))
    return sorted_results[:max_results]

def vol_link(vol_num):
    return f"[[volumes/volume-{vol_num:02d}|כרך {vol_num}]]"

def sicha_link(vol_num, slug, display_title):
    # Title format: "נח · כרך 1 · א" — first part is parsha name
    parts = display_title.split('·')
    if len(parts) >= 1:
        name = parts[0].strip()
    else:
        name = display_title
    # Clean up quotes from frontmatter
    name = name.strip('"\'').strip()
    # If still looks like "כרך N", use slug instead
    if name.startswith('כרך') or not name:
        name = slug.replace('_', ' ').replace('-', ' ')
    return f"[[sichos/vol{vol_num:02d}/{slug}|{name}]]"

def build_table_rows(matches):
    rows = []
    for m in matches:
        vol = m["vol"]
        excerpt = m["excerpt"] or "—"
        link = sicha_link(vol, m["slug"], m["title"])
        rows.append(f"| {vol_link(vol)} | {link} | {m['page']} | {excerpt} |")
    return '\n'.join(rows)

def write_concept(filepath, title_heb, title_eng, desc_heb, tags, matches, total_count=None):
    """Write a concept article."""
    slug = filepath.stem
    if total_count is None:
        total_count = len(matches)

    count_display = f"**{total_count} שיחות** עוסקות בנושא זה בליקוטי שיחות"
    if total_count == 0:
        count_display = "לא נמצאו שיחות ספציפיות בנושא זה בליקוטי שיחות"

    table_header = "| כרך | שיחה | עמ' | תוכן |\n|-----|------|-----|------|"
    rows = build_table_rows(matches)

    tags_str = '\n'.join(f'  - {t}' for t in tags)

    table_section = ""
    if matches:
        table_section = f"""
## עיקרי הנושא בליקוטי שיחות

{table_header}
{rows}"""

    content = f"""---
title: '{title_heb} — ליקוטי שיחות'
tags:
{tags_str}
---

# {title_heb}

> **{title_eng}**
>
> {desc_heb}

{count_display}
{table_section}

---

*[[concepts/index|← כל המושגים]] · [[index|ראשי]]*
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"  Wrote {filepath.name} ({total_count} matches, showing {len(matches)})")


# ============================================================
# STEP 3: Define all 98 concepts with patterns and metadata
# ============================================================

CONCEPTS = [
    {
        "file": "achashverosh.md",
        "title_heb": "אחשורוש",
        "title_eng": "Achashverosh — King of Persia",
        "desc_heb": "אחשורוש מלך פרס — דמותו בסיפור המגילה ועניינו הרוחני",
        "tags": ["concept", "achashverosh", "ענינים-מיוחדים", "likkutei-sichos"],
        "patterns": [r"אחשורוש", r"מלך פרס", r"מגילה.*מלך", r"אחשור"],
    },
    {
        "file": "achdut-hashem.md",
        "title_heb": "אחדות ה'",
        "title_eng": "Unity of G-d",
        "desc_heb": "ה' אחד — אחדות האמיתית של הקדוש ברוך הוא, שאין עוד מלבדו",
        "tags": ["concept", "achdut-hashem", "אמונה", "likkutei-sichos"],
        "patterns": [r"אחדות.*ה'|אחדות.*אלוקים|אחדות.*השם", r"אין עוד מלבדו", r"ה' אחד", r"יחיד ומיוחד", r"אחדות הבורא"],
    },
    {
        "file": "adam-harishon.md",
        "title_heb": "אדם הראשון",
        "title_eng": "Adam — The First Man",
        "desc_heb": "אדם הראשון — אבי כל החי, חטאו ותיקונו",
        "tags": ["concept", "adam-harishon", "אבות-ואמהות", "likkutei-sichos"],
        "patterns": [r"אדם הראשון", r"אדם.*גן עדן", r"חטא.*אדם", r"אדם.*חוה", r"אדה\"ר"],
    },
    {
        "file": "aggadah.md",
        "title_heb": "אגדה",
        "title_eng": "Aggadah — Rabbinic Narrative",
        "desc_heb": "אגדות חז\"ל — הסיפורים והמדרשים של חכמינו ז\"ל ועניינם הפנימי",
        "tags": ["concept", "aggadah", "תורה-שבעל-פה", "likkutei-sichos"],
        "patterns": [r"אגד(?:ה|ות)", r"מדרש.*אגד", r"חז\"ל.*אגד", r"ענין האגד"],
    },
    {
        "file": "ahavat-hashem.md",
        "title_heb": "אהבת ה'",
        "title_eng": "Love of G-d",
        "desc_heb": "אהבת ה' — מצוות ואהבת את ה' אלקיך, עמוד עבודת הלב",
        "tags": ["concept", "ahavat-hashem", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"אהבת ה'|אהבת השם|אהבת.*אלקים|אהבת אלוקים", r"ואהבת את ה'", r"אהבה.*עבודת הלב", r"אהבה.*בכל לבבך"],
    },
    {
        "file": "ahavat-yisrael.md",
        "title_heb": "אהבת ישראל",
        "title_eng": "Love of Fellow Jews",
        "desc_heb": "ואהבת לרעך כמוך — אהבת כל אחד מישראל, כלל גדול בתורה",
        "tags": ["concept", "ahavat-yisrael", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"אהבת ישראל", r"ואהבת לרעך כמוך", r"אהבת.*אחיו", r"אהבת.*חברו"],
    },
    {
        "file": "ainei-golah.md",
        "title_heb": "עיני הגולה",
        "title_eng": "Eyes of the Exile — Leading Sages",
        "desc_heb": "עיני הגולה — גדולי ישראל שהיו עיני העדה בתקופת הגלות",
        "tags": ["concept", "ainei-golah", "גדולי-ישראל", "likkutei-sichos"],
        "patterns": [r"עיני הגולה", r"עיני.*גולה", r"גדולי הגולה"],
    },
    {
        "file": "akudim.md",
        "title_heb": "עקודים",
        "title_eng": "Akudim — Bound Lights",
        "desc_heb": "עולם העקודים — אחד הארבעה עולמות הקדמונים בתורת הקבלה",
        "tags": ["concept", "akudim", "קבלה", "likkutei-sichos"],
        "patterns": [r"עקודים", r"עולם העקודים", r"עקוד.*נקוד.*טלוי"],
    },
    {
        "file": "alef-bet.md",
        "title_heb": "אלף-בית",
        "title_eng": "Hebrew Alphabet",
        "desc_heb": "אותיות האלף-בית העבריות — כלים אלוקיים לבריאת העולם",
        "tags": ["concept", "alef-bet", "תורה", "likkutei-sichos"],
        "patterns": [r"אלף.?בית", r"אותיות.*עברי", r"כ\"ב אותיות", r"אות.*עברי", r"אותיות.*תורה"],
    },
    {
        "file": "aliya-leregel.md",
        "title_heb": "עלייה לרגל",
        "title_eng": "Pilgrimage to Jerusalem",
        "desc_heb": "עלייה לרגל לבית המקדש שלש פעמים בשנה — ראיה, חגיגה ושמחה",
        "tags": ["concept", "aliya-leregel", "מועדים", "likkutei-sichos"],
        "patterns": [r"עלי(?:ה|ת) לרגל", r"שלש רגלים", r"יראה.*מקדש", r"חג.*עלי[יה]"],
    },
    {
        "file": "alma-igalia-alma-itkasya.md",
        "title_heb": "עלמא דאתגליא ועלמא דאתכסיא",
        "title_eng": "Revealed World and Hidden World",
        "desc_heb": "עלמא דאתגליא — העולם הנגלה; עלמא דאתכסיא — העולם הנסתר",
        "tags": ["concept", "alma-igalia-alma-itkasya", "קבלה", "likkutei-sichos"],
        "patterns": [r"עלמא דאתגל[יא]+", r"עלמא דאתכסי[א]+", r"נגלה ונסתר.*עולם", r"עולם.*נסתר.*נגלה"],
    },
    {
        "file": "alter-rebbe.md",
        "title_heb": "אדמו\"ר הזקן",
        "title_eng": "The Alter Rebbe — Rabbi Shneur Zalman",
        "desc_heb": "רבי שניאור זלמן מליאדי — מייסד חסידות חב\"ד, בעל התניא והשו\"ע",
        "tags": ["concept", "alter-rebbe", "חב\"ד", "likkutei-sichos"],
        "patterns": [r"אדמו\"ר הזקן", r"רבי שניאור זלמן", r"בעל התניא", r"אדה\"ז", r"בעל הלוח", r"רש\"ז"],
    },
    {
        "file": "am-yisrael.md",
        "title_heb": "עם ישראל",
        "title_eng": "The Jewish People",
        "desc_heb": "עם ישראל — עם סגולה, ממלכת כהנים וגוי קדוש",
        "tags": ["concept", "am-yisrael", "ישראל", "likkutei-sichos"],
        "patterns": [r"עם ישראל", r"כנסת ישראל", r"בני ישראל", r"עם סגולה", r"ממלכת כהנים"],
    },
    {
        "file": "amram.md",
        "title_heb": "עמרם",
        "title_eng": "Amram — Father of Moses",
        "desc_heb": "עמרם — אבי משה רבינו, אהרן ומרים",
        "tags": ["concept", "amram", "אבות-ואמהות", "likkutei-sichos"],
        "patterns": [r"עמרם", r"עמרם.*אב.*משה", r"עמרם ויוכבד"],
    },
    {
        "file": "anavah-shfillut.md",
        "title_heb": "ענוה ושפלות",
        "title_eng": "Humility and Lowliness",
        "desc_heb": "ענוה ושפלות — שתי מדרגות בהכנעת האדם לפני קונו",
        "tags": ["concept", "anavah-shfillut", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"ענוה.*שפלות|שפלות.*ענוה", r"שפל.*רוח", r"מדת הענוה", r"ענוה.*הכנעה"],
    },
    {
        "file": "anavah.md",
        "title_heb": "ענוה",
        "title_eng": "Humility",
        "desc_heb": "ענוה — מדת הענוה, להיות שפל ונבזה בעיני עצמו",
        "tags": ["concept", "anavah", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"ענוה", r"ענו.*מאד", r"מדת הענוה", r"ענו כמשה"],
    },
    {
        "file": "anokhi.md",
        "title_heb": "אנכי",
        "title_eng": "Anochi — I Am the Lord",
        "desc_heb": "אנכי ה' אלקיך — הדיבר הראשון, גילוי עצמות בסיני",
        "tags": ["concept", "anokhi", "תורה", "likkutei-sichos"],
        "patterns": [r"אנכי ה'|אנכי.*ה' אלקיך", r"ענין אנכי", r"אנכי.*עשרת הדברות", r"דיבר.*אנכי"],
    },
    {
        "file": "arba-minim.md",
        "title_heb": "ארבעה מינים",
        "title_eng": "Four Species",
        "desc_heb": "ארבעת המינים — אתרוג, לולב, הדס וערבה, מצות חג הסוכות",
        "tags": ["concept", "arba-minim", "מועדים", "likkutei-sichos"],
        "patterns": [r"ארבעה? מינים|ד' מינים", r"לולב.*אתרוג", r"אתרוג.*הדס.*ערבה", r"נטילת לולב"],
    },
    {
        "file": "aretz.md",
        "title_heb": "ארץ ישראל",
        "title_eng": "Land of Israel",
        "desc_heb": "ארץ ישראל — ארץ הקודש, נחלת עם ישראל",
        "tags": ["concept", "aretz", "ישראל", "likkutei-sichos"],
        "patterns": [r"ארץ ישראל", r"ארץ.*קדושה", r"ארץ.*הקדש", r"נחלת.*ישראל", r"א\"י"],
    },
    {
        "file": "aron.md",
        "title_heb": "ארון הקודש",
        "title_eng": "Holy Ark",
        "desc_heb": "ארון הברית — ארון העדות שבמשכן ובמקדש, מקום השראת השכינה",
        "tags": ["concept", "aron", "מקדש", "likkutei-sichos"],
        "patterns": [r"ארון.*קדש|ארון.*ברית|ארון.*עדות", r"ארון ה'", r"כפורת.*ארון", r"הארון"],
    },
    {
        "file": "arvit.md",
        "title_heb": "ערבית",
        "title_eng": "Evening Prayer",
        "desc_heb": "תפילת ערבית — תפילת הלילה, רשות אם חובה",
        "tags": ["concept", "arvit", "תפילה", "likkutei-sichos"],
        "patterns": [r"ערבית", r"תפילת ערב", r"מעריב", r"תפלת הלילה"],
    },
    {
        "file": "asara-maamarot.md",
        "title_heb": "עשרה מאמרות",
        "title_eng": "Ten Utterances of Creation",
        "desc_heb": "עשרה מאמרות — בעשרה מאמרות נברא העולם",
        "tags": ["concept", "asara-maamarot", "בריאה", "likkutei-sichos"],
        "patterns": [r"עשרה מאמרות|י' מאמרות", r"בעשרה מאמרות נברא", r"מאמרות.*בריאה"],
    },
    {
        "file": "ataph-khafoch.md",
        "title_heb": "אתהפכא",
        "title_eng": "Transformation — Turning Darkness to Light",
        "desc_heb": "אתהפכא חשוכא לנהורא — המרת החושך לאור, הרע לטוב",
        "tags": ["concept", "ataph-khafoch", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"אתהפכא", r"חשוכא לנהורא", r"הפיכת.*חושך.*אור|אתהפכא.*חשוכא"],
    },
    {
        "file": "atik.md",
        "title_heb": "עתיק",
        "title_eng": "Atik Yomin — Ancient of Days",
        "desc_heb": "עתיק יומין — הפרצוף הגבוה ביותר בעולם האצילות בתורת הקבלה",
        "tags": ["concept", "atik", "קבלה", "likkutei-sichos"],
        "patterns": [r"עתיק יומין|עתיק", r"אריך.*עתיק", r"כתר.*עתיק"],
    },
    {
        "file": "atzilut.md",
        "title_heb": "אצילות",
        "title_eng": "World of Emanation",
        "desc_heb": "עולם האצילות — הגבוה שבארבעת העולמות, אצילות קדושה",
        "tags": ["concept", "atzilut", "קבלה", "likkutei-sichos"],
        "patterns": [r"עולם האצילות|אצילות", r"בחינת.*אצילות", r"עולמות.*אצילות", r"אצי' |אצי\"ל"],
    },
    {
        "file": "atzvut.md",
        "title_heb": "עצבות",
        "title_eng": "Sadness / Melancholy",
        "desc_heb": "עצבות — מניעת העבודה, ניגוד לשמחה",
        "tags": ["concept", "atzvut", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"עצבות", r"עצב.*לב|לב.*עצב", r"מרה שחורה", r"עצבות.*עבודה"],
    },
    {
        "file": "av-chodesh.md",
        "title_heb": "אב (חודש)",
        "title_eng": "Month of Av",
        "desc_heb": "חודש אב — חודש האבל על חורבן בית המקדש",
        "tags": ["concept", "av-chodesh", "מועדים", "likkutei-sichos"],
        "patterns": [r"חודש.*אב(?!\s*ובן)", r"תשעה באב|ט' באב", r"בין המצרים", r"ספד.*אב|אב.*ספד"],
    },
    {
        "file": "av-uven.md",
        "title_heb": "אב ובן",
        "title_eng": "Father and Son",
        "desc_heb": "יחס אב ובן — הקשר בין האב לבנו, בגשמיות וברוחניות",
        "tags": ["concept", "av-uven", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"אב ובן|אב.*בן(?!.*אד)", r"יחס.*אב.*בן", r"ביחס.*בן.*לאב", r"אב.*ולדו"],
    },
    {
        "file": "aveilut.md",
        "title_heb": "אבלות",
        "title_eng": "Mourning",
        "desc_heb": "אבלות — דיני ומנהגי האבל, ועניינם הרוחני",
        "tags": ["concept", "aveilut", "הלכה", "likkutei-sichos"],
        "patterns": [r"אבלות", r"אבל.*שבעה", r"שבעת ימי אבל", r"דיני אבלות"],
    },
    {
        "file": "avoda-zara.md",
        "title_heb": "עבודה זרה",
        "title_eng": "Idolatry",
        "desc_heb": "עבודה זרה — אסור לעבוד אלוהים אחרים, אחד משלש עברות החמורות",
        "tags": ["concept", "avoda-zara", "הלכה", "likkutei-sichos"],
        "patterns": [r"עבודה זרה", r"ע\"ז", r"עבוד.*אלהים אחרים", r"פסל.*ותמונה"],
    },
    {
        "file": "avodah-begashmius.md",
        "title_heb": "עבודה בגשמיות",
        "title_eng": "Divine Service in Physical Matters",
        "desc_heb": "עבודת ה' בגשמיות — עלאיית הגשמיות לקדושה",
        "tags": ["concept", "avodah-begashmius", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"עבודה בגשמיות|עבוד[ה]? בגשמי", r"גשמיות.*עבודה", r"ענינים גשמיים.*עבודה"],
    },
    {
        "file": "avodat-habeinonim.md",
        "title_heb": "עבודת הבינוניים",
        "title_eng": "Divine Service of the Beinoni",
        "desc_heb": "עבודת הבינוני — עבודתו המיוחדת של הבינוני בתפילה ובמחשבה",
        "tags": ["concept", "avodat-habeinonim", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"עבודת הבינוני|עבודת.*בינוני", r"בינוני.*עבוד", r"מדרגת הבינוני.*עבוד"],
    },
    {
        "file": "avodat-halev.md",
        "title_heb": "עבודת הלב",
        "title_eng": "Service of the Heart — Prayer",
        "desc_heb": "עבודה שבלב — תפילה, אהבה ויראה",
        "tags": ["concept", "avodat-halev", "תפילה", "likkutei-sichos"],
        "patterns": [r"עבודה שבלב|עבודת הלב", r"תפלה.*עבוד.*לב", r"עבוד.*לב", r"לב.*עבוד"],
    },
    {
        "file": "avot.md",
        "title_heb": "אבות",
        "title_eng": "The Patriarchs",
        "desc_heb": "האבות הקדושים — אברהם יצחק ויעקב, מרכבה לאלוקות",
        "tags": ["concept", "avot", "אבות-ואמהות", "likkutei-sichos"],
        "patterns": [r"האבות(?! של)", r"שלשה אבות|ג' אבות", r"אבות.*מרכבה", r"אברהם יצחק ויעקב"],
    },
    {
        "file": "avraham.md",
        "title_heb": "אברהם",
        "title_eng": "Abraham our Father",
        "desc_heb": "אברהם אבינו — מידת החסד, ראש האבות הקדושים",
        "tags": ["concept", "avraham", "אבות-ואמהות", "likkutei-sichos"],
        "patterns": [r"אברהם אבינו", r"אברהם.*אב|א\"א(?:\s|$)", r"נסיונות.*אברהם", r"חסד.*אברהם", r"מדת.*אברהם"],
    },
    {
        "file": "azmut.md",
        "title_heb": "עצמות",
        "title_eng": "The Essence of G-d",
        "desc_heb": "עצמות אין סוף — עצמות ממש של הקב\"ה, למעלה מגדרי הספירות",
        "tags": ["concept", "azmut", "קבלה", "likkutei-sichos"],
        "patterns": [r"עצמות.*אין סוף|עצמות.*א\"ס|עצמות ומהות", r"עצמות.*ממש", r"ענין העצמות"],
    },
    {
        "file": "baal-shem-tov.md",
        "title_heb": "בעל שם טוב",
        "title_eng": "The Baal Shem Tov",
        "desc_heb": "רבי ישראל בעל שם טוב — מייסד תנועת החסידות",
        "tags": ["concept", "baal-shem-tov", "חסידות", "likkutei-sichos"],
        "patterns": [r"בעל שם טוב|הבעש\"ט|הבעל שם טוב", r"רבי ישראל.*בעל שם", r"מייסד.*חסידות.*בעל שם"],
    },
    {
        "file": "bar-mitzva.md",
        "title_heb": "בר מצוה",
        "title_eng": "Bar Mitzvah",
        "desc_heb": "בר מצוה — גיל המצוות לבן, י\"ג שנה",
        "tags": ["concept", "bar-mitzva", "חינוך", "likkutei-sichos"],
        "patterns": [r"בר מצוה", r"גיל.*מצוות.*בן|בן.*י\"ג", r"בן י\"ג שנה"],
    },
    {
        "file": "basar-chalav.md",
        "title_heb": "בשר וחלב",
        "title_eng": "Meat and Milk — Kosher Laws",
        "desc_heb": "לא תבשל גדי בחלב אמו — איסור בשר וחלב",
        "tags": ["concept", "basar-chalav", "הלכה", "likkutei-sichos"],
        "patterns": [r"בשר.*חלב|חלב.*בשר", r"לא תבשל גדי", r"איסור.*בשר.*חלב"],
    },
    {
        "file": "bat-kol.md",
        "title_heb": "בת קול",
        "title_eng": "Heavenly Voice",
        "desc_heb": "בת קול — קול אלוקי המתגלה בעולם",
        "tags": ["concept", "bat-kol", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"בת קול", r"קול.*שמים", r"קול.*אלוקי"],
    },
    {
        "file": "bchol-meodcha.md",
        "title_heb": "בכל מאדך",
        "title_eng": "With All Your Might",
        "desc_heb": "ואהבת את ה' אלקיך בכל מאדך — אהבת ה' ללא גבולות",
        "tags": ["concept", "bchol-meodcha", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"בכל מאדך", r"מאד.*אהבה", r"ואהבת.*מאדך"],
    },
    {
        "file": "beer-sheva.md",
        "title_heb": "באר שבע",
        "title_eng": "Beer Sheva",
        "desc_heb": "באר שבע — עיר האבות, מקום שביעת הבארות",
        "tags": ["concept", "beer-sheva", "ארץ-ישראל", "likkutei-sichos"],
        "patterns": [r"באר שבע", r"בארה שבע"],
    },
    {
        "file": "behira.md",
        "title_heb": "בחירה חפשית",
        "title_eng": "Free Choice",
        "desc_heb": "בחירה חפשית — כוח הבחירה שניתן לאדם",
        "tags": ["concept", "behira", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"בחירה חפשית|בחיר[ה]? חופשי", r"כוח הבחירה", r"בחירת האדם"],
    },
    {
        "file": "beinoni.md",
        "title_heb": "בינוני",
        "title_eng": "Beinoni — The Intermediate Person",
        "desc_heb": "מדרגת הבינוני — מדרגת הבינוני בתניא, אחר הצדיק ולפני הרשע",
        "tags": ["concept", "beinoni", "דרגות-עבודה", "likkutei-sichos"],
        "patterns": [r"בינוני", r"מדרגת הבינוני", r"הבינוני.*תניא", r"בינוני.*צדיק.*רשע"],
    },
    {
        "file": "beit-hakvarot.md",
        "title_heb": "בית הקברות",
        "title_eng": "Cemetery",
        "desc_heb": "בית הקברות — בית עולמם של הנפטרים",
        "tags": ["concept", "beit-hakvarot", "הלכה", "likkutei-sichos"],
        "patterns": [r"בית הקברות|בית עלמין", r"קברות", r"קבר.*אבות"],
    },
    {
        "file": "beit-hamikdash.md",
        "title_heb": "בית המקדש",
        "title_eng": "Holy Temple",
        "desc_heb": "בית המקדש — בית הבחירה, מקום השראת השכינה",
        "tags": ["concept", "beit-hamikdash", "מקדש", "likkutei-sichos"],
        "patterns": [r"בית המקדש|בית הבחירה", r"מקדש.*ירושלים", r"בנין המקדש", r"בהמ\"ק"],
    },
    {
        "file": "beit-knesset.md",
        "title_heb": "בית כנסת",
        "title_eng": "Synagogue",
        "desc_heb": "בית הכנסת — מקדש מעט, מקום התפילה",
        "tags": ["concept", "beit-knesset", "תפילה", "likkutei-sichos"],
        "patterns": [r"בית הכנסת|בית כנסת", r"מקדש מעט", r"שיל|שול"],
    },
    {
        "file": "ben-azai.md",
        "title_heb": "בן עזאי",
        "title_eng": "Ben Azzai — Talmudic Sage",
        "desc_heb": "שמעון בן עזאי — תנא, הסתייג מנישואין ומסר נפשו לתורה",
        "tags": ["concept", "ben-azai", "גדולי-ישראל", "likkutei-sichos"],
        "patterns": [r"בן עזאי", r"שמעון בן עזאי"],
    },
    {
        "file": "ben-noach.md",
        "title_heb": "בן נח",
        "title_eng": "Noahide — Non-Jewish Laws",
        "desc_heb": "שבע מצוות בני נח — חובות האנושות שלא ממעמד ישראל",
        "tags": ["concept", "ben-noach", "הלכה", "likkutei-sichos"],
        "patterns": [r"בן נח|בני נח", r"ז' מצוות.*נח|שבע מצוות.*נח", r"נכרי.*מצוות"],
    },
    {
        "file": "berachah.md",
        "title_heb": "ברכה",
        "title_eng": "Blessing",
        "desc_heb": "ברכה — ברכות הנהנין, המצוות והשבח, המשכת שפע אלוקי",
        "tags": ["concept", "berachah", "הלכה", "likkutei-sichos"],
        "patterns": [r"ברכה", r"ברכות.*הנהנין", r"מברך.*ה'", r"ענין הברכה"],
    },
    {
        "file": "beria.md",
        "title_heb": "בריאה",
        "title_eng": "World of Creation",
        "desc_heb": "עולם הבריאה — השני מארבעת העולמות",
        "tags": ["concept", "beria", "קבלה", "likkutei-sichos"],
        "patterns": [r"עולם הבריאה", r"בריאה.*יצירה.*עשיה", r"בחינת הבריאה"],
    },
    {
        "file": "bilha.md",
        "title_heb": "בלהה",
        "title_eng": "Bilhah — Handmaid of Rachel",
        "desc_heb": "בלהה — שפחת רחל, אם דן ונפתלי",
        "tags": ["concept", "bilha", "אבות-ואמהות", "likkutei-sichos"],
        "patterns": [r"בלהה", r"בלהה.*שפחת", r"בלהה.*דן.*נפתלי"],
    },
    {
        "file": "binyamin.md",
        "title_heb": "בנימין",
        "title_eng": "Benjamin — Tribe of Israel",
        "desc_heb": "בנימין — בנו הצעיר של יעקב, שבט בנימין",
        "tags": ["concept", "binyamin", "שבטי-ישראל", "likkutei-sichos"],
        "patterns": [r"בנימין", r"שבט בנימין", r"בן.*ימין"],
    },
    {
        "file": "bishvil.md",
        "title_heb": "בשבילי נברא העולם",
        "title_eng": "The World was Created for My Sake",
        "desc_heb": "בשבילי נברא העולם — כל אחד מישראל חייב לומר לשמי נברא העולם",
        "tags": ["concept", "bishvil", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"בשבילי נברא", r"לשמי נברא העולם", r"כל אחד.*עולם נברא"],
    },
    {
        "file": "bittul.md",
        "title_heb": "ביטול",
        "title_eng": "Nullification / Self-Abnegation",
        "desc_heb": "ביטול היש — ביטול הרצון העצמי בפני רצון השם",
        "tags": ["concept", "bittul", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"ביטול", r"בטל.*עצמו|בטל.*אני", r"ביטול היש", r"ביטל.*בפני"],
    },
    {
        "file": "bitul-berov.md",
        "title_heb": "ביטול ברוב",
        "title_eng": "Nullification by Majority",
        "desc_heb": "ביטול ברוב — דין הלכתי של ביטול איסור בתוך היתר",
        "tags": ["concept", "bitul-berov", "הלכה", "likkutei-sichos"],
        "patterns": [r"ביטול ברוב", r"בטל ברוב", r"ביטול.*ששים"],
    },
    {
        "file": "borer-birur.md",
        "title_heb": "בורר — בירור",
        "title_eng": "Sorting — Clarification",
        "desc_heb": "בורר — מלאכת בורר בשבת; ובירור — עבודת הבירורים בחסידות",
        "tags": ["concept", "borer-birur", "הלכה", "likkutei-sichos"],
        "patterns": [r"בורר|מלאכת בורר", r"ביר[ו]?ר.*ניצוצות|עבודת הביר[ו]?ר", r"ברירה.*שבת"],
    },
    {
        "file": "bria-yesh-meayin.md",
        "title_heb": "בריאה יש מאין",
        "title_eng": "Creation ex nihilo",
        "desc_heb": "יש מאין — בריאת העולם מאין מוחלט, חידוש מוחלט",
        "tags": ["concept", "bria-yesh-meayin", "בריאה", "likkutei-sichos"],
        "patterns": [r"יש מאין", r"בריאה.*יש מאין|יש מאין.*בריאה", r"חידוש העולם"],
    },
    {
        "file": "bria-yetzira-asiya.md",
        "title_heb": "בריאה יצירה עשייה",
        "title_eng": "Creation, Formation, Action",
        "desc_heb": "עולמות בי\"ע — בריאה, יצירה, עשיה — שלשת העולמות",
        "tags": ["concept", "bria-yetzira-asiya", "קבלה", "likkutei-sichos"],
        "patterns": [r"בריאה.*יצירה.*עשי[ה]?|בי\"ע", r"עולמות.*בי\"ע", r"עולם.*יצירה"],
    },
    {
        "file": "brit-avraham.md",
        "title_heb": "ברית אברהם",
        "title_eng": "Covenant of Abraham",
        "desc_heb": "ברית מילה — ברית אברהם אבינו, אות הברית",
        "tags": ["concept", "brit-avraham", "מצוות", "likkutei-sichos"],
        "patterns": [r"ברית אברהם|ברית.*אברהם", r"אות הברית", r"ברית.*מילה.*אברהם"],
    },
    {
        "file": "brit-institution.md",
        "title_heb": "ברית",
        "title_eng": "Covenant — Sacred Bond",
        "desc_heb": "ברית — ברית ה' עם ישראל, הקשר הנצחי",
        "tags": ["concept", "brit-institution", "מצוות", "likkutei-sichos"],
        "patterns": [r"ברית ה'|ברית.*ישראל", r"כרת ברית", r"ענין הברית"],
    },
    {
        "file": "brit-milah.md",
        "title_heb": "ברית מילה",
        "title_eng": "Circumcision",
        "desc_heb": "ברית מילה — מצות מילה, אות ברית קודש",
        "tags": ["concept", "brit-milah", "מצוות", "likkutei-sichos"],
        "patterns": [r"ברית מילה|מילה", r"מצות מילה", r"מל.*ברית"],
    },
    {
        "file": "briut.md",
        "title_heb": "בריאות",
        "title_eng": "Health",
        "desc_heb": "בריאות הגוף — שמירת הבריאות כמצוה",
        "tags": ["concept", "briut", "הלכה", "likkutei-sichos"],
        "patterns": [r"בריאות", r"בריאת הגוף", r"שמירת הבריאות"],
    },
    {
        "file": "chalom.md",
        "title_heb": "חלום",
        "title_eng": "Dream",
        "desc_heb": "חלומות — חלום שלישית הנבואה, ועניינם ברוחניות",
        "tags": ["concept", "chalom", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"חלום", r"חלומות", r"חלמתי.*חלום", r"חלם.*לילה"],
    },
    {
        "file": "chanah-rebbetzin.md",
        "title_heb": "רבנית חנה",
        "title_eng": "Rebbetzin Chana — Mother of the Rebbe",
        "desc_heb": "הרבנית חנה — אמו של הרבי מליובאוויטש",
        "tags": ["concept", "chanah-rebbetzin", "חב\"ד", "likkutei-sichos"],
        "patterns": [r"הרבנית חנה|רבנית.*חנה", r"אמו.*רבי.*חנה"],
    },
    {
        "file": "chanukah.md",
        "title_heb": "חנוכה",
        "title_eng": "Chanukah — Festival of Lights",
        "desc_heb": "חנוכה — חג האורות, ניצחון בית חשמונאי",
        "tags": ["concept", "chanukah", "מועדים", "likkutei-sichos"],
        "patterns": [r"חנוכה", r"נרות חנוכה|חנוכיה", r"חשמונאי", r"פך השמן"],
    },
    {
        "file": "chasidut.md",
        "title_heb": "חסידות",
        "title_eng": "Chassidus",
        "desc_heb": "פנימיות התורה — תורת החסידות שגילה הבעל שם טוב",
        "tags": ["concept", "chasidut", "חסידות", "likkutei-sichos"],
        "patterns": [r"חסידות|תורת החסידות", r"פנימיות התורה", r"דרך החסידות"],
    },
    {
        "file": "chatan.md",
        "title_heb": "חתן",
        "title_eng": "Bridegroom",
        "desc_heb": "חתן — חיוביו ושמחתו ביום חתונתו",
        "tags": ["concept", "chatan", "הלכה", "likkutei-sichos"],
        "patterns": [r"חתן", r"חתן.*כלה|חתנים", r"חופה.*חתן"],
    },
    {
        "file": "chatik-nevela.md",
        "title_heb": "חתיכה נבלה",
        "title_eng": "Prohibited Piece",
        "desc_heb": "חתיכה הראויה להתכבד — חתיכה הנעשית נבלה",
        "tags": ["concept", "chatik-nevela", "הלכה", "likkutei-sichos"],
        "patterns": [r"חתיכה.*נבל[ה]?|חתיכה הראויה", r"נבלה.*חתיכה"],
    },
    {
        "file": "chayim.md",
        "title_heb": "חיים",
        "title_eng": "Life",
        "desc_heb": "חיים — ענין החיות האלוקית, חיי האדם",
        "tags": ["concept", "chayim", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"חיים.*אלוקי|חיות אלוקי", r"ענין החיים", r"חיי האדם.*נשמה"],
    },
    {
        "file": "chazir.md",
        "title_heb": "חזיר",
        "title_eng": "Pig — Non-Kosher Animal",
        "desc_heb": "חזיר — הבהמה הטמאה, שמחזיר טלפיים ואינו מעלה גרה",
        "tags": ["concept", "chazir", "הלכה", "likkutei-sichos"],
        "patterns": [r"חזיר", r"מחזיר טלפיים", r"טמאה.*חזיר"],
    },
    {
        "file": "chazkiyahu.md",
        "title_heb": "חזקיהו",
        "title_eng": "Hezekiah — King of Judah",
        "desc_heb": "חזקיהו מלך יהודה — ביטל לימוד תורה מדן ועד באר שבע",
        "tags": ["concept", "chazkiyahu", "גדולי-ישראל", "likkutei-sichos"],
        "patterns": [r"חזקיהו", r"חזקיהו.*מלך"],
    },
    {
        "file": "chesed-gevura-tiferet.md",
        "title_heb": "חסד גבורה תפארת",
        "title_eng": "Kindness, Strength, Beauty",
        "desc_heb": "ספירות חג\"ת — חסד גבורה ותפארת, מידות הלב",
        "tags": ["concept", "chesed-gevura-tiferet", "קבלה", "likkutei-sichos"],
        "patterns": [r"חסד.*גבורה.*תפארת|ג\"ת|חג\"ת", r"ספירת חסד", r"ספירות.*חג\"ת"],
    },
    {
        "file": "cheshbon-nefesh.md",
        "title_heb": "חשבון הנפש",
        "title_eng": "Soul Accounting",
        "desc_heb": "חשבון הנפש — בדיקת מעשיו וחשיבתם",
        "tags": ["concept", "cheshbon-nefesh", "עבודת-ה", "likkutei-sichos"],
        "patterns": [r"חשבון הנפש|חשבון.*נפש", r"לחשוב.*מעשיו", r"בדיקת.*מעשים"],
    },
    {
        "file": "cheshmal.md",
        "title_heb": "חשמל",
        "title_eng": "Chashmal — Mystical Concept",
        "desc_heb": "חשמל — ענין קבלי, גבול חכמה ובינה",
        "tags": ["concept", "cheshmal", "קבלה", "likkutei-sichos"],
        "patterns": [r"חשמל", r"ענין.*חשמל"],
    },
    {
        "file": "cheshvan.md",
        "title_heb": "חשון",
        "title_eng": "Month of Cheshvan",
        "desc_heb": "חודש מרחשון — חודש ללא מועדים",
        "tags": ["concept", "cheshvan", "מועדים", "likkutei-sichos"],
        "patterns": [r"חשו?ן|מרחשון", r"חודש.*חשון"],
    },
    {
        "file": "chevron.md",
        "title_heb": "חברון",
        "title_eng": "Hebron",
        "desc_heb": "חברון — עיר האבות, מקום מערת המכפלה",
        "tags": ["concept", "chevron", "ארץ-ישראל", "likkutei-sichos"],
        "patterns": [r"חברון", r"מערת המכפלה", r"קרית ארבע"],
    },
    {
        "file": "chinuch-banim.md",
        "title_heb": "חינוך בנים",
        "title_eng": "Education of Children",
        "desc_heb": "חינוך הבנים — חנוך לנער על פי דרכו",
        "tags": ["concept", "chinuch-banim", "חינוך", "likkutei-sichos"],
        "patterns": [r"חינוך הבנים|חינוך.*ילדים|חנוך.*נער", r"גידול הבנים", r"בנים.*חינוך"],
    },
    {
        "file": "chinuch.md",
        "title_heb": "חינוך",
        "title_eng": "Education",
        "desc_heb": "חינוך — חינוך לתורה ומצוות",
        "tags": ["concept", "chinuch", "חינוך", "likkutei-sichos"],
        "patterns": [r"חינוך", r"מצות חינוך", r"חנוך לנער"],
    },
    {
        "file": "chitas.md",
        "title_heb": "חת\"ת",
        "title_eng": "Chitas — Daily Torah Study",
        "desc_heb": "חומש תהלים תניא — לימוד יומי שתיקן הרבי",
        "tags": ["concept", "chitas", "חב\"ד", "likkutei-sichos"],
        "patterns": [r"חת\"ת", r"חומש.*תהלים.*תניא", r"לימוד יומי.*חומש"],
    },
    {
        "file": "chochma-bina-daat.md",
        "title_heb": "חכמה בינה דעת",
        "title_eng": "Wisdom, Understanding, Knowledge",
        "desc_heb": "חב\"ד — חכמה בינה ודעת, ספירות המוחין",
        "tags": ["concept", "chochma-bina-daat", "קבלה", "likkutei-sichos"],
        "patterns": [r"חכמה.*בינה.*דעת|חב\"ד(?!\.)|מוחין.*חב\"ד", r"ספירות.*חב\"ד", r"חכמה.*בינה"],
    },
    {
        "file": "chodesh-hadasha.md",
        "title_heb": "חודש החדשה",
        "title_eng": "The Month of Renewal",
        "desc_heb": "החודש הזה לכם — ראש חודשים, חידוש הלבנה",
        "tags": ["concept", "chodesh-hadasha", "מועדים", "likkutei-sichos"],
        "patterns": [r"החודש הזה לכם", r"ראש חדשים", r"חידוש הלבנה"],
    },
    {
        "file": "chodesh-rosh-chodesh.md",
        "title_heb": "ראש חודש",
        "title_eng": "Rosh Chodesh — New Month",
        "desc_heb": "ראש חודש — ראש כל חודש, קדוש מן התורה",
        "tags": ["concept", "chodesh-rosh-chodesh", "מועדים", "likkutei-sichos"],
        "patterns": [r"ראש חודש|ר\"ח", r"קידוש החודש", r"מצות ראש חודש"],
    },
    {
        "file": "chukim.md",
        "title_heb": "חוקים",
        "title_eng": "Divine Decrees",
        "desc_heb": "חוקים — מצוות שאין להם טעם גלוי, ועיקר קיומם מחמת ציוי ה'",
        "tags": ["concept", "chukim", "מצוות", "likkutei-sichos"],
        "patterns": [r"חוקים|חוק.*מצוה", r"מצות.*חוק", r"גזירת הכתוב"],
    },
    {
        "file": "chutznik.md",
        "title_heb": "חוצניק",
        "title_eng": "Outsider / Non-Lubavitch",
        "desc_heb": "חוצניק — כינוי לאחד שאינו מחסידי חב\"ד",
        "tags": ["concept", "chutznik", "חסידות", "likkutei-sichos"],
        "patterns": [r"חוצניק", r"חצוניים.*חסידות"],
    },
    {
        "file": "conservative.md",
        "title_heb": "קונסרבטיבים",
        "title_eng": "Conservative Movement",
        "desc_heb": "תנועת קונסרבטיבית — גישה ביהדות המודרנית",
        "tags": ["concept", "conservative", "יהדות-מודרנית", "likkutei-sichos"],
        "patterns": [r"קונסרבטיב", r"conservative", r"יהדות.*קונסרבטיב"],
    },
    {
        "file": "dagim.md",
        "title_heb": "דגים",
        "title_eng": "Fish",
        "desc_heb": "דגים — עם ישראל נמשל לדגים; דגים כשרים",
        "tags": ["concept", "dagim", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"דגים", r"ישראל.*דגים|דגים.*ישראל", r"נמשל.*דגים"],
    },
    {
        "file": "david.md",
        "title_heb": "דוד המלך",
        "title_eng": "King David",
        "desc_heb": "דוד המלך — מלך ישראל, כותב התהלים",
        "tags": ["concept", "david", "גדולי-ישראל", "likkutei-sichos"],
        "patterns": [r"דוד המלך|דוד.*מלך", r"בית דוד", r"דוד.*תהלים", r"מלכות.*דוד"],
    },
    {
        "file": "dibbur.md",
        "title_heb": "דיבור",
        "title_eng": "Speech",
        "desc_heb": "כוח הדיבור — כלי גילוי ויצירה",
        "tags": ["concept", "dibbur", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"כוח הדיבור|ענין הדיבור", r"דיבור.*לשון", r"כח הדיבור"],
    },
    {
        "file": "dina.md",
        "title_heb": "דינה",
        "title_eng": "Dinah — Daughter of Jacob",
        "desc_heb": "דינה — בת יעקב, ענינה בתורה",
        "tags": ["concept", "dina", "אבות-ואמהות", "likkutei-sichos"],
        "patterns": [r"דינה(?:.*בת יעקב)?", r"ענין דינה"],
    },
    {
        "file": "dira-betachtonim.md",
        "title_heb": "דירה בתחתונים",
        "title_eng": "Dwelling in the Lower Worlds",
        "desc_heb": "המטרה האלוקית — לעשות לו יתברך דירה בתחתונים",
        "tags": ["concept", "dira-betachtonim", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"דירה בתחתונים", r"לעשות.*דירה.*תחתונים", r"תכלית הבריאה.*דירה"],
    },
    {
        "file": "dirah-betachtonim.md",
        "title_heb": "דירה בתחתונים",
        "title_eng": "Dwelling in the Lower Worlds — Extended",
        "desc_heb": "דירה בתחתונים — ביאור נוסף, תכלית ירידת הנשמה",
        "tags": ["concept", "dirah-betachtonim", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"דירה בתחתונים", r"לעשות.*דירה.*תחתונים", r"תכלית הבריאה.*דירה"],
    },
    {
        "file": "dor-haflaga.md",
        "title_heb": "דור הפלגה",
        "title_eng": "Generation of the Dispersion",
        "desc_heb": "דור הפלגה — בונה מגדל בבל",
        "tags": ["concept", "dor-haflaga", "תנ\"ך", "likkutei-sichos"],
        "patterns": [r"דור הפלגה", r"מגדל בבל", r"דור.*מגדל"],
    },
    {
        "file": "dothan.md",
        "title_heb": "דותן",
        "title_eng": "Dothan",
        "desc_heb": "דותן — המקום שמכרו שם את יוסף",
        "tags": ["concept", "dothan", "תנ\"ך", "likkutei-sichos"],
        "patterns": [r"דותן", r"דות[י]?נה"],
    },
    {
        "file": "dovber-magid.md",
        "title_heb": "המגיד ממעזריטש",
        "title_eng": "The Maggid of Mezeritch",
        "desc_heb": "רבי דוב בר ממעזריטש — ממשיך הבעל שם טוב",
        "tags": ["concept", "dovber-magid", "חסידות", "likkutei-sichos"],
        "patterns": [r"המגיד ממעזריטש|המגיד.*מעזריטש", r"רבי דוב בר", r"ר' דובבר"],
    },
    {
        "file": "dovber-mitteler.md",
        "title_heb": "אדמו\"ר האמצעי",
        "title_eng": "The Mitteler Rebbe",
        "desc_heb": "רבי דוב בר שניאורסון — אדמו\"ר האמצעי",
        "tags": ["concept", "dovber-mitteler", "חב\"ד", "likkutei-sichos"],
        "patterns": [r"אדמו\"ר האמצעי|המתיר שניאורסון", r"רבי דובבר.*בנו", r"אדה\"א"],
    },
    {
        "file": "dug.md",
        "title_heb": "דג",
        "title_eng": "Fish — Symbolic Meaning",
        "desc_heb": "דג — סמל ברכה ופריה ורביה",
        "tags": ["concept", "dug", "יסודות-החסידות", "likkutei-sichos"],
        "patterns": [r"(?:ה|ו)דג(?!\s*ים)", r"סמל.*דג", r"ברכה.*דג"],
    },
    {
        "file": "dvar.md",
        "title_heb": "דבר",
        "title_eng": "Word / Thing",
        "desc_heb": "דבר — דיבור ה', דברי תורה",
        "tags": ["concept", "dvar", "תורה", "likkutei-sichos"],
        "patterns": [r"דבר ה'|דבר.*תורה", r"דיבור.*השם", r"דברו.*ה'"],
    },
]

# ============================================================
# STEP 4: Process all concepts
# ============================================================

print(f"\nProcessing {len(CONCEPTS)} concepts...")

for concept in CONCEPTS:
    filepath = CONCEPTS_DIR / concept["file"]
    matches_all = find_matches(concept["patterns"], sicha_data, max_results=100)
    total_count = len(matches_all)
    matches_display = matches_all[:50]

    write_concept(
        filepath=filepath,
        title_heb=concept["title_heb"],
        title_eng=concept["title_eng"],
        desc_heb=concept["desc_heb"],
        tags=concept["tags"],
        matches=matches_display,
        total_count=total_count,
    )

print("\nDone! All concepts written.")
