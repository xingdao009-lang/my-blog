import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "content" / "site.json"
DATA_DIR = BASE_DIR / "site" / "data"

DEFAULTS = {
    "site_name": "Tax & AI Brief",
    "brand_mark": "T",
    "tagline": "Tax · Finance · AI",
    "hero_title": "Tax, finance and AI in one clear brief.",
    "hero_subtitle": "",
    "about_title": "About",
    "about_lead": "",
    "name": "Owner",
    "role": "",
    "bio": "",
    "focus": [],
    "contact": "",
    "avatar": "T",
    "footer_text": "Tax & AI Brief",
    "accent": "#1d4ed8",
    "theme": "business-blue",
}


def main():
    settings = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        loaded = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        settings.update(loaded)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dumped = json.dumps(settings, ensure_ascii=False, indent=2)
    (DATA_DIR / "site.json").write_text(dumped + "\n", encoding="utf-8")
    (DATA_DIR / "site-data.js").write_text("window.SITE_DATA = " + dumped + ";\n", encoding="utf-8")
    print("profile data written")


if __name__ == "__main__":

    main()