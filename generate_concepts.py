#!/usr/bin/env python3
"""
Extract Chassidic/Torah concepts from all Likkutei Sichos and build concept pages.
Uses regex pattern matching against a comprehensive predefined concept list.
Scans the existing per-sicha .md files under content/sichos/volNN/.
"""
import os, re, json
from pathlib import Path
from collections import defaultdict

SRC = Path('/workspace/group/likkutei-sichos-wiki/content/sichos')
OUT = Path('/workspace/group/likkutei-sichos-wiki/content')
(OUT / 'concepts').mkdir(exist_ok=True)

# ── Comprehensive concept dictionary ────────────────────────────────────────
# Format: slug → {he: Hebrew name, en: English, category: category, patterns: [regex patterns]}
CONCEPTS = {
    # ── Chassidic Core Concepts ─────────────────────────────────────────────
    'dira-betachtonim': {
        'he': 'דירה בתחתונים', 'en': 'Dwelling in the Lower Worlds',
        'category': 'יסודות החסידות',
        'desc': 'המטרה האלוקית של בריאת העולם — לעשות לו יתברך דירה בתחתונים',
        'patterns': ['דירה בתחתונ', 'דירה להקב"ה', 'דירה לו ית']
    },
    'bittul': {
        'he': 'ביטול', 'en': 'Nullification / Self-Abnegation',
        'category': 'עבודת ה\'',
        'desc': 'ביטול היש — ביטול הרצון העצמי בפני רצון השם',
        'patterns': ['ביטול היש', 'ביטול עצמ', 'ביטול לאלוקות', 'ביטל']
    },
    'ataph-khafoch': {
        'he': 'אתהפכא', 'en': "Ithapcha — transformation of darkness to light",
        'category': 'עבודת ה\'',
        'desc': 'אתהפכא חשוכא לנהורא — המרת הרע לטוב, החושך לאור',
        'patterns': ['אתהפכא', 'חשוכא לנהורא', 'ממרירו למיתקא']
    },
    'iskafya': {
        'he': 'אתכפיא', 'en': "Ithkafya — subduing the animal soul",
        'category': 'עבודת ה\'',
        'desc': 'אתכפיא — כיבוש היצר, כפיית הנפש הבהמית',
        'patterns': ['אתכפיא', 'כפיית', 'כיבוש הנפש הבהמית']
    },
    'nefesh-habehamit': {
        'he': 'נפש הבהמית', 'en': 'Animal Soul',
        'category': 'נפשות',
        'desc': 'הנפש הבהמית — נפש החיונית הכוללת את המידות הרעות',
        'patterns': ['נפש הבהמית', 'נפשו הבהמית', 'הנפש הבהמי']
    },
    'nefesh-haelohit': {
        'he': 'נפש האלוקית', 'en': 'Divine Soul',
        'category': 'נפשות',
        'desc': 'הנפש האלוקית — חלק אלוק ממעל ממש',
        'patterns': ['נפש האלוקית', 'נפשו האלוקית', 'הנפש האלוק']
    },
    'nefesh-hasichlit': {
        'he': 'נפש השכלית', 'en': 'Intellectual Soul',
        'category': 'נפשות',
        'desc': 'הנפש השכלית — הנפש השכלית הממוצעת',
        'patterns': ['נפש השכלית', 'נפשו השכלית']
    },
    'sefirot': {
        'he': 'ספירות', 'en': 'Sefirot',
        'category': 'קבלה',
        'desc': 'עשר ספירות — כלים וכוחות אלוקיים',
        'patterns': ['הספירות', 'עשר ספיר', 'ספירת ה', 'ספירות עליונ']
    },
    'chochma-bina-daat': {
        'he': 'חב"ד', 'en': "Chabad — Chochma, Bina, Daat",
        'category': 'קבלה וחסידות',
        'desc': 'חכמה בינה דעת — שלוש המוחין',
        'patterns': ['חכמה בינה דעת', 'חב"ד', 'שלשה מוחין', 'המוחין']
    },
    'chesed-gevura-tiferet': {
        'he': 'חסד גבורה תפארת', 'en': 'Chesed, Gevura, Tiferet',
        'category': 'קבלה',
        'desc': 'שש המידות — חסד גבורה תפארת נצח הוד יסוד',
        'patterns': ['חסד גבורה', 'שש מידות', 'שש ספירות', 'ו קצוות']
    },
    'ohr-einsof': {
        'he': 'אור אין סוף', 'en': 'Ohr Ein Sof — Infinite Light',
        'category': 'קבלה',
        'desc': 'אור אין סוף ב"ה — האור האלוקי הבלתי מוגבל',
        'patterns': ['אור אין סוף', 'א"ס ב"ה', 'אין סוף ברוך', 'אוא"ס']
    },
    'tzimtzum': {
        'he': 'צמצום', 'en': 'Tzimtzum — Divine Contraction',
        'category': 'קבלה',
        'desc': 'הצמצום — כיווץ האור האלוקי לצורך בריאת העולם',
        'patterns': ['הצמצום', 'ענין הצמצום', 'אחר הצמצום', 'קודם הצמצום']
    },
    'klipot': {
        'he': 'קליפות', 'en': 'Klipot — Husks / Forces of Evil',
        'category': 'קבלה',
        'desc': 'קליפות — כוחות הטומאה וחיצוניות',
        'patterns': ['הקליפות', 'ענין הקליפה', 'קליפת', 'כוחות הטומאה']
    },
    'galut-geula': {
        'he': 'גלות וגאולה', 'en': 'Exile and Redemption',
        'category': 'גאולה',
        'desc': 'ענין הגלות והגאולה — גלות ישראל וגאולה האמיתית',
        'patterns': ['גלות וגאולה', 'ענין הגלות', 'ענין הגאולה', 'גאולה האמיתית', 'גאולה השלמה']
    },
    'moshiach': {
        'he': 'משיח', 'en': 'Moshiach',
        'category': 'גאולה',
        'desc': 'ביאת המשיח — גאולה האמיתית והשלמה',
        'patterns': ['ביאת המשיח', 'ימות המשיח', 'מלך המשיח', 'משיח צדקנו']
    },
    'teshuvah': {
        'he': 'תשובה', 'en': 'Teshuvah — Repentance',
        'category': 'עבודת ה\'',
        'desc': 'ענין התשובה — חזרה בתשובה ותיקון החטא',
        'patterns': ['ענין התשובה', 'עבודת התשובה', 'בעל תשובה', 'תשובה עילאה', 'תשובה תתאה']
    },
    'tefila': {
        'he': 'תפילה', 'en': 'Prayer',
        'category': 'עבודת ה\'',
        'desc': 'עבודת התפילה — עבודה שבלב',
        'patterns': ['עבודת התפלה', 'ענין התפלה', 'עבודת הלב', 'כוונת התפלה']
    },
    'torah': {
        'he': 'תורה', 'en': 'Torah Study',
        'category': 'עבודת ה\'',
        'desc': 'לימוד התורה — תורה לשמה ועסק התורה',
        'patterns': ['לימוד התורה', 'תורה לשמה', 'עסק התורה', 'תורה שבכתב', 'תורה שבעל פה']
    },
    'mitzvot': {
        'he': 'מצוות', 'en': 'Mitzvot',
        'category': 'עבודת ה\'',
        'desc': 'קיום המצוות — תרי"ג מצוות',
        'patterns': ['תרי"ג מצוות', 'קיום המצוות', 'עשיית המצוות', 'מצות עשה', 'מצות לא תעשה']
    },
    'ahavat-hashem': {
        'he': 'אהבת ה\'', 'en': "Love of G-d",
        'category': 'עבודת ה\'',
        'desc': 'אהבת ה\' — ואהבת את ה\' אלקיך',
        'patterns': ['אהבת ה\'', 'אהבת אלוקים', 'ואהבת את ה', 'אהבה לה\'', 'אהבה רבה', 'אהבת עולם']
    },
    'yirat-hashem': {
        'he': 'יראת ה\'', 'en': "Fear of G-d",
        'category': 'עבודת ה\'',
        'desc': 'יראת ה\' — יראה עילאה ויראה תתאה',
        'patterns': ['יראת ה\'', 'יראת שמים', 'יראה עילאה', 'יראה תתאה', 'יראת הרוממות']
    },
    'simcha': {
        'he': 'שמחה', 'en': 'Joy',
        'category': 'עבודת ה\'',
        'desc': 'ענין השמחה — עבדו את ה\' בשמחה',
        'patterns': ['ענין השמחה', 'שמחה אמיתית', 'עבדו את ה\' בשמחה', 'שמחה של מצוה']
    },
    'tzaddik': {
        'he': 'צדיק', 'en': 'Tzaddik',
        'category': 'דרגות עבודה',
        'desc': 'מדרגת הצדיק — צדיק גמור',
        'patterns': ['מדרגת הצדיק', 'צדיק גמור', 'ענין הצדיק', 'צדיקים גמורים']
    },
    'beinoni': {
        'he': 'בינוני', 'en': 'Beinoni — Intermediate Person',
        'category': 'דרגות עבודה',
        'desc': 'מדרגת הבינוני — מדרגת הבינוני בתניא',
        'patterns': ['מדרגת הבינוני', 'ענין הבינוני', 'הבינוני שבתניא', 'בינוני']
    },
    'four-worlds': {
        'he': 'ד\' עולמות', 'en': 'Four Worlds — ABYA',
        'category': 'קבלה',
        'desc': 'ארבעה עולמות — אצילות בריאה יצירה עשיה',
        'patterns': ['ד\' עולמות', 'ארבעה עולמות', 'אצילות בריאה יצירה עשיה', 'עולם האצילות', 'עולם הבריאה']
    },
    'atzilut': {
        'he': 'עולם האצילות', 'en': "World of Atzilut",
        'category': 'קבלה',
        'desc': 'עולם האצילות — העולם הראשון',
        'patterns': ['עולם האצילות', 'בעולם האצילות', 'בחינת האצילות']
    },
    'pardes': {
        'he': 'פרד"ס', 'en': "PaRDeS — Four Levels of Torah Interpretation",
        'category': 'תורה',
        'desc': 'פשט רמז דרוש סוד — ארבע דרגות פירוש התורה',
        'patterns': ['פשט רמז דרוש סוד', 'פרד"ס', 'סוד הפשט', 'ענין הפשט', 'ענין הסוד']
    },
    'rashi': {
        'he': 'רש"י', 'en': "Rashi",
        'category': 'פרשנים',
        'desc': 'פירוש רש"י על התורה',
        'patterns': ['פירוש רש"י', 'רש"י מפרש', 'דברי רש"י', 'לפי רש"י', 'קושיית רש"י']
    },
    'rambam': {
        'he': 'רמב"ם', 'en': "Rambam",
        'category': 'פרשנים',
        'desc': 'הרמב"ם — משנה תורה ומורה נבוכים',
        'patterns': ['הרמב"ם', 'לשון הרמב"ם', 'שיטת הרמב"ם', 'דעת הרמב"ם']
    },
    'alter-rebbe': {
        'he': 'אדמו"ר הזקן', 'en': "Alter Rebbe",
        'category': 'נשיאי חב"ד',
        'desc': 'אדמו"ר הזקן — רבי שניאור זלמן מליאדי, בעל התניא',
        'patterns': ['אדמו"ר הזקן', 'רבינו הזקן', 'בעל התניא', 'בעל הצ"צ']
    },
    'tanya': {
        'he': 'תניא', 'en': "Tanya",
        'category': 'ספרי חסידות',
        'desc': 'ספר התניא — לקוטי אמרים לאדמו"ר הזקן',
        'patterns': ['ספר התניא', 'בתניא', 'לשון התניא', 'כמבואר בתניא']
    },
    'torah-or': {
        'he': 'תורה אור', 'en': "Torah Ohr",
        'category': 'ספרי חסידות',
        'desc': 'ספר תורה אור — מאמרי אדמו"ר הזקן',
        'patterns': ['תורה אור', 'בתורה אור', 'בד"ה', 'בדרוש', 'לקוטי תורה']
    },
    'zohar': {
        'he': 'זוהר', 'en': "Zohar",
        'category': 'קבלה',
        'desc': 'ספר הזוהר — ספר הזוהר הקדוש',
        'patterns': ['בזוהר', 'הזוהר הקדוש', 'זוהר אומר', 'לשון הזוהר', 'ספר הזוהר']
    },
    'baal-shem-tov': {
        'he': 'הבעש"ט', 'en': "Baal Shem Tov",
        'category': 'נשיאי חסידות',
        'desc': 'הבעל שם טוב — מייסד תנועת החסידות',
        'patterns': ['הבעש"ט', 'הבעל שם טוב', 'רבי ישראל בעש"ט', 'תורת הבעש"ט']
    },
    'hashgacha-pratit': {
        'he': 'השגחה פרטית', 'en': "Divine Providence",
        'category': 'אמונה',
        'desc': 'השגחה פרטית — השגחת ה\' על כל פרט',
        'patterns': ['השגחה פרטית', 'ענין ההשגחה', 'השגחתו ית\'', 'השגחה אלוקית']
    },
    'emuna': {
        'he': 'אמונה', 'en': "Faith / Emunah",
        'category': 'אמונה',
        'desc': 'ענין האמונה — אמונה בה\' אחד',
        'patterns': ['ענין האמונה', 'אמונה שלמה', 'כח האמונה', 'בדרך אמונה']
    },
    'achdut-hashem': {
        'he': 'אחדות ה\'', 'en': "Unity of G-d",
        'category': 'אמונה',
        'desc': 'ה\' אחד — אחדות האמיתית',
        'patterns': ['אחדות ה\'', 'ה\' אחד', 'אחדות האמיתית', 'יחוד האמיתי', 'אין עוד מלבדו']
    },
    'bria-yesh-meayin': {
        'he': 'בריאה יש מאין', 'en': "Creation Ex Nihilo",
        'category': 'קבלה',
        'desc': 'בריאת העולם יש מאין — בריאה מאפס המוחלט',
        'patterns': ['יש מאין', 'יש מאפס', 'מאין ואפס', 'בריאת יש מאין', 'מאפס המוחלט']
    },
    'iskafya-ishapu': {
        'he': 'כלי ואור', 'en': "Vessels and Light",
        'category': 'קבלה',
        'desc': 'כלים ואורות — יחס האור לכלי',
        'patterns': ['כלים ואורות', 'הכלי והאור', 'ענין הכלי', 'ממלא כל עלמין', 'סובב כל עלמין']
    },
    'mmale-sovev': {
        'he': 'ממלא וסובב', 'en': "Memale and Sovev",
        'category': 'קבלה',
        'desc': 'ממלא כל עלמין וסובב כל עלמין',
        'patterns': ['ממלא כל עלמין', 'סובב כל עלמין', 'ממלא וסובב']
    },
    'avodat-habeinonim': {
        'he': 'עבודת הבינונים', 'en': "Service of the Beinonim",
        'category': 'עבודת ה\'',
        'desc': 'עבודת הבינונים — עבודה בדרך כלל',
        'patterns': ['עבודת הבינוני', 'ענין עבודה', 'עבודה בפועל', 'עבודת האדם']
    },
    'klal-yisrael': {
        'he': 'כלל ישראל', 'en': "The Jewish People",
        'category': 'ישראל',
        'desc': 'כלל ישראל — הקשר המיוחד בין ישראל לה\'',
        'patterns': ['כלל ישראל', 'עם ישראל', 'בני ישראל', 'נשמות ישראל', 'ישראל ואורייתא']
    },
    'matan-torah': {
        'he': 'מתן תורה', 'en': "Giving of the Torah",
        'category': 'תורה',
        'desc': 'מעמד הר סיני — מתן תורה',
        'patterns': ['מתן תורה', 'מעמד הר סיני', 'קבלת התורה', 'זמן מתן תורתנו']
    },
    'beit-hamikdash': {
        'he': 'בית המקדש', 'en': "Holy Temple",
        'category': 'מקדש',
        'desc': 'בית המקדש — בית הבחירה',
        'patterns': ['בית המקדש', 'בית הבחירה', 'המשכן', 'השכינה שורה', 'קדש הקדשים']
    },
    'avoda-zara': {
        'he': 'עבודה זרה', 'en': "Idolatry",
        'category': 'הלכה',
        'desc': 'איסור עבודה זרה',
        'patterns': ['עבודה זרה', 'ע"ז', 'פולחן']
    },
    'gehinnom-gan-eden': {
        'he': 'גן עדן וגיהנם', 'en': "Paradise and Hell",
        'category': 'עולם הבא',
        'desc': 'גן עדן וגיהנם — גמול ועונש',
        'patterns': ['גן עדן', 'גיהנם', 'עולם הבא', 'שכר ועונש']
    },
    'teshuva-ilaa': {
        'he': 'תשובה עילאה', 'en': "Higher Teshuvah",
        'category': 'עבודת ה\'',
        'desc': 'תשובה עילאה — מדרגת תשובה של צדיקים',
        'patterns': ['תשובה עילאה', 'תשובה תתאה', 'תשובה עליונה', 'מדרגת התשובה']
    },
    'kavanah': {
        'he': 'כוונה', 'en': "Intention / Kavvanah",
        'category': 'עבודת ה\'',
        'desc': 'ענין הכוונה — כוונה במצוות ובתפילה',
        'patterns': ['ענין הכוונה', 'כוונת הלב', 'כוונה שלמה', 'כוונה אמיתית']
    },
    'middot': {
        'he': 'מידות', 'en': "Character Traits / Middot",
        'category': 'עבודת ה\'',
        'desc': 'עבודת המידות — תיקון המידות',
        'patterns': ['תיקון המידות', 'עבודת המידות', 'מידות טובות', 'שבע המידות']
    },
    'hiskashrus': {
        'he': 'התקשרות', 'en': "Hiskashrus — Attachment to the Rebbe",
        'category': 'חסידות',
        'desc': 'ענין ההתקשרות — התקשרות לנשיא הדור',
        'patterns': ['ענין ההתקשרות', 'התקשרות לרבי', 'התקשרות לנשיא', 'נשיא הדור']
    },
    'shabbat': {
        'he': 'שבת', 'en': "Shabbat",
        'category': 'מועדים',
        'desc': 'קדושת השבת — שבת קודש',
        'patterns': ['קדושת השבת', 'ענין השבת', 'שבת קודש', 'כבוד שבת']
    },
    'avodah-begashmius': {
        'he': 'עבודה בגשמיות', 'en': "Divine Service in Physical Life",
        'category': 'עבודת ה\'',
        'desc': 'עשיית הגשמיות לכלי לאלוקות',
        'patterns': ['בגשמיות', 'ענינים גשמיים', 'עסקים גשמיים', 'חיי היום יום']
    },
    'lishma': {
        'he': 'לשמה', 'en': "Lishmah — For its own sake",
        'category': 'עבודת ה\'',
        'desc': 'עבודה לשמה — לשם שמים',
        'patterns': ['לשמה', 'לשם שמים', 'שלא לשמה', 'תורה לשמה']
    },
    'memshalah': {
        'he': 'ממשלה', 'en': "Dominion / Rule",
        'category': 'קבלה',
        'desc': 'ממשלת האדם על כוחותיו',
        'patterns': ['ממשלת', 'שליטה על', 'מושל ב']
    },
    'chasidut': {
        'he': 'חסידות', 'en': "Chassidus",
        'category': 'חסידות',
        'desc': 'פנימיות התורה — תורת החסידות',
        'patterns': ['פנימיות התורה', 'תורת החסידות', 'חסידות חב"ד', 'ענין החסידות', 'לימוד החסידות']
    },
    'alef-bet': {
        'he': 'אותיות', 'en': "Hebrew Letters",
        'category': 'תורה',
        'desc': 'קדושת האותיות — אותיות התורה',
        'patterns': ['אותיות התורה', 'קדושת האותיות', 'כח האות', 'אות ה']
    },
    'hishtalshelut': {
        'he': 'השתלשלות', 'en': "Chain of Being",
        'category': 'קבלה',
        'desc': 'סדר השתלשלות — ירידת האור האלוקי',
        'patterns': ['סדר ההשתלשלות', 'השתלשלות העולמות', 'ירידת האור', 'ירידת העולמות']
    },
    'yechida': {
        'he': 'יחידה', 'en': "Yechida — Highest Soul Level",
        'category': 'נפשות',
        'desc': 'חמשה חלקי הנפש — נפש רוח נשמה חיה יחידה',
        'patterns': ['נפש רוח נשמה חיה יחידה', 'חמשה בחינות', 'בחינת היחידה', 'בחינת הנשמה']
    },
    'malchut': {
        'he': 'מלכות', 'en': "Malchut — Kingship",
        'category': 'קבלה',
        'desc': 'ספירת המלכות — מלכות שמים',
        'patterns': ['ספירת המלכות', 'מלכות שמים', 'בחינת המלכות', 'קבלת מלכות']
    },
    'kedusha-tumah': {
        'he': 'קדושה וטומאה', 'en': "Holiness and Impurity",
        'category': 'קבלה',
        'desc': 'ענין הקדושה והטומאה',
        'patterns': ['קדושה וטומאה', 'ענין הקדושה', 'סטרא דקדושה', 'צד הקדושה']
    },
    'avodat-halev': {
        'he': 'עבודת הלב', 'en': "Service of the Heart",
        'category': 'עבודת ה\'',
        'desc': 'עבודה שבלב — זו תפילה',
        'patterns': ['עבודת הלב', 'עבודה שבלב', 'בלב שלם']
    },
    'anavah': {
        'he': 'ענוה', 'en': "Humility",
        'category': 'מידות',
        'desc': 'ענין הענוה — מאד מאד הוי שפל רוח',
        'patterns': ['ענין הענוה', 'שפלות', 'ענוה אמיתית', 'שפל רוח']
    },
    'ahavat-yisrael': {
        'he': 'אהבת ישראל', 'en': "Love of Fellow Jews",
        'category': 'מידות',
        'desc': 'ואהבת לרעך כמוך — אהבת ישראל',
        'patterns': ['אהבת ישראל', 'ואהבת לרעך', 'אחדות ישראל', 'כלל ישראל']
    },
    'tzedakah': {
        'he': 'צדקה', 'en': "Charity",
        'category': 'מצוות',
        'desc': 'מצות הצדקה — גדולה צדקה',
        'patterns': ['מצות הצדקה', 'ענין הצדקה', 'גדולה צדקה', 'נתינת צדקה']
    },
    'keter': {
        'he': 'כתר', 'en': "Keter — Crown",
        'category': 'קבלה',
        'desc': 'ספירת הכתר — כתר עליון',
        'patterns': ['ספירת הכתר', 'כתר עליון', 'בחינת הכתר', 'מדרגת הכתר']
    },
    'histapkut': {
        'he': 'הסתפקות', 'en': "Contentment",
        'category': 'מידות',
        'desc': 'ענין ההסתפקות — הסתפקות במועט',
        'patterns': ['הסתפקות', 'שמח בחלקו', 'הסתפקות במועט']
    },
    'penimiyut-chitzoniyut': {
        'he': 'פנימיות וחיצוניות', 'en': "Inner and Outer",
        'category': 'קבלה',
        'desc': 'פנימיות וחיצוניות — הבדל בין הכוחות',
        'patterns': ['פנימיות וחיצוניות', 'פנימיות הכוחות', 'חיצוניות הכוחות', 'פנים וחוץ']
    },
}

# ── Scan all sicha .md files ─────────────────────────────────────────────────
print("Scanning sicha texts for concepts...")

# Map: concept_slug → list of match dicts
concept_matches = defaultdict(list)

all_md_files = sorted(SRC.rglob('*.md'))
total_files = len(all_md_files)
done = 0

for md_path in all_md_files:
    # Extract vol number from parent dir name like vol01, vol02, etc.
    vol_dir = md_path.parent.name  # e.g. "vol01"
    m_vol = re.search(r'\d+', vol_dir)
    vol_n = int(m_vol.group()) if m_vol else 0

    # Stem is like "bereishit_1" or "ki-tetzei_4"
    stem = md_path.stem  # e.g. "bereishit_1"
    # Split on last underscore to get slug and part
    m_stem = re.match(r'^(.+?)_(\d+)$', stem)
    if m_stem:
        topic_slug = m_stem.group(1)
        part_num = m_stem.group(2)
    else:
        topic_slug = stem
        part_num = '1'

    page_slug = f"{topic_slug}_{part_num}"

    # Read content
    text = md_path.read_text(encoding='utf-8', errors='replace')

    # Extract page number from frontmatter/header line "# חלק N — עמ' PAGE"
    page_m = re.search(r"עמ['']\s*(\d+)", text)
    page = int(page_m.group(1)) if page_m else 0

    # Extract Hebrew topic name from title line
    title_m = re.search(r'^#\s+(.+?)(?:\s+·|\s*$)', text, re.MULTILINE)
    topic_he = title_m.group(1).strip() if title_m else topic_slug

    for concept_slug, concept in CONCEPTS.items():
        for pat in concept['patterns']:
            if re.search(pat, text):
                concept_matches[concept_slug].append({
                    'vol': vol_n,
                    'page': page,
                    'page_slug': page_slug,
                    'topic_he': topic_he,
                    'topic_slug': topic_slug,
                    'vol_dir': vol_dir,
                })
                break  # only count once per concept per sicha

    done += 1
    if done % 100 == 0:
        print(f"  Scanned {done}/{total_files}...")

print(f"Scanning complete. Found concepts in {sum(len(v) for v in concept_matches.values())} sicha-concept pairs")

# ── Generate concept pages ───────────────────────────────────────────────────
for concept_slug, matches in sorted(concept_matches.items()):
    if not matches:
        continue
    concept = CONCEPTS[concept_slug]

    # Sort by volume then page
    matches_sorted = sorted(matches, key=lambda x: (x['vol'], x['page']))

    # Build table rows
    rows = []
    for m in matches_sorted:
        vol_link = f"[[volumes/volume-{m['vol']:02d}|כרך {m['vol']}]]"
        if m['page_slug']:
            sicha_link = f"[[sichos/{m['vol_dir']}/{m['page_slug']}|{m['topic_he']}]]"
        else:
            sicha_link = m['topic_he']
        rows.append(f"| {vol_link} | {sicha_link} | {m['page']} |")

    table = "| כרך | שיחה | עמ' |\n|-----|------|-----|\n" + '\n'.join(rows)

    # Category tag — sanitize for YAML
    cat_slug = re.sub(r'[^\w\-]', '', concept['category'].replace(' ', '-').replace("'", '').replace('"', ''))

    # YAML-safe title: use single quotes, escape any single quotes inside
    safe_title = f"{concept['he']} — ליקוטי שיחות".replace("'", "''")

    content = f"""---
title: '{safe_title}'
tags:
  - concept
  - {concept_slug}
  - {cat_slug}
  - likkutei-sichos
---

# {concept['he']}

> **{concept['en']}**
>
> {concept['desc']}

**{len(matches)} שיחות** דנות בנושא זה

## שיחות העוסקות ב{concept['he']}

{table}

---

*[[concepts/index|← כל המושגים]] · [[index|ראשי]]*
"""
    (OUT / 'concepts' / f'{concept_slug}.md').write_text(content, encoding='utf-8')

print(f"Generated {len(concept_matches)} concept pages")

# ── Generate concepts index ──────────────────────────────────────────────────
by_category = defaultdict(list)
for slug, matches in concept_matches.items():
    c = CONCEPTS[slug]
    by_category[c['category']].append((slug, c['he'], c['en'], len(matches)))

cat_sections = []
for cat, items in sorted(by_category.items()):
    items_sorted = sorted(items, key=lambda x: -x[3])  # sort by count desc
    rows = [f"| [[concepts/{sl}|{he}]] | {en} | {cnt} |" for sl, he, en, cnt in items_sorted]
    table = "| מושג | Concept | שיחות |\n|------|---------|-------|\n" + '\n'.join(rows)
    cat_sections.append(f"## {cat}\n\n{table}")

total_pairs = sum(len(v) for v in concept_matches.values())

(OUT / 'concepts' / 'index.md').write_text(f"""---
title: 'מפתח המושגים — ליקוטי שיחות'
tags:
  - concepts
  - likkutei-sichos
---

# מפתח המושגים והרעיונות

מדריך שיטתי למושגים החסידיים והתורניים המרכזיים בליקוטי שיחות.

**{len(concept_matches)} מושגים** · **{total_pairs} אזכורים**

{chr(10).join(cat_sections)}

---

*[[index|ראשי]]*
""", encoding='utf-8')

print("Generated concepts index")

# ── Save concept manifest ─────────────────────────────────────────────────────
concept_manifest = {
    slug: {
        'he': CONCEPTS[slug]['he'],
        'en': CONCEPTS[slug]['en'],
        'category': CONCEPTS[slug]['category'],
        'count': len(matches)
    }
    for slug, matches in concept_matches.items()
}
with open(OUT.parent / 'concept_manifest.json', 'w', encoding='utf-8') as f:
    json.dump(concept_manifest, f, ensure_ascii=False, indent=2)

import subprocess
result = subprocess.run(['find', str(OUT), '-name', '*.md'], capture_output=True, text=True)
total_md = len([l for l in result.stdout.strip().split('\n') if l])
print(f"\nDone! Total .md files: {total_md}")
print(f"   Concept pages: {len(concept_matches)}")
print("Top 10 concepts by sicha count:")
for slug, matches in sorted(concept_matches.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"   {CONCEPTS[slug]['he']}: {len(matches)}")
