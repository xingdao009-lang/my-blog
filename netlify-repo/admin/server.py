#!/usr/bin/env python3
"""Local content backend for the tax/AI static site.

The server binds to 127.0.0.1 by default and has no external dependencies.
The first visit asks the owner to create a password. Settings are stored in
content/site.json and are mirrored to site/data for the public static pages.
"""

import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sys
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = BASE_DIR / "site"
ADMIN_DIR = BASE_DIR / "admin"
CONTENT_DIR = BASE_DIR / "content"
ADMIN_FILE = CONTENT_DIR / "admin.json"
SETTINGS_FILE = CONTENT_DIR / "site.json"
DATA_DIR = SITE_DIR / "data"
COOKIE_NAME = "csg_admin_session"
SESSION_TTL = 8 * 3600
MAX_BODY = 1024 * 1024
SESSIONS = {}

DEFAULT_SETTINGS = {
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

TEXT_FIELDS = (
    "site_name", "brand_mark", "tagline", "hero_title", "hero_subtitle",
    "about_title", "about_lead", "name", "role", "bio", "contact",
    "avatar", "footer_text",
)
ALLOWED_THEMES = {"business-blue", "midnight", "slate"}
ACCENT_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_settings():
    data = dict(DEFAULT_SETTINGS)
    loaded = read_json(SETTINGS_FILE, {})
    if isinstance(loaded, dict):
        data.update(loaded)
    return data


def write_profile_data(settings):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dumped = json.dumps(settings, ensure_ascii=False, indent=2)
    atomic_write(DATA_DIR / "site.json", dumped + "\n")
    atomic_write(DATA_DIR / "site-data.js", "window.SITE_DATA = " + dumped + ";\n")


def clean_settings(payload):
    if not isinstance(payload, dict):
        raise ValueError("设置内容格式不正确")

    result = {}
    for key in TEXT_FIELDS:
        value = payload.get(key, DEFAULT_SETTINGS[key])
        if not isinstance(value, str):
            raise ValueError("{} 必须是文本".format(key))
        result[key] = value.strip()[:20000]

    focus = payload.get("focus", [])
    if isinstance(focus, str):
        focus = [item.strip() for item in focus.split(",")]
    if not isinstance(focus, list):
        raise ValueError("focus 必须是列表")
    result["focus"] = [str(item).strip()[:80] for item in focus if str(item).strip()][:8]

    accent = str(payload.get("accent", DEFAULT_SETTINGS["accent"])).strip()
    if not ACCENT_RE.match(accent):
        raise ValueError("主色调必须是 #RRGGBB 格式")
    result["accent"] = accent

    theme = str(payload.get("theme", DEFAULT_SETTINGS["theme"])).strip()
    if theme not in ALLOWED_THEMES:
        raise ValueError("主题选项不正确")
    result["theme"] = theme
    return result


def password_hash(password, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210000)
    return salt.hex(), digest.hex()


def verify_password(password, record):
    try:
        _, digest = password_hash(password, record.get("salt", ""))
        return hmac.compare_digest(digest, record.get("hash", ""))
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = "CSGContentAdmin/1.0"

    def log_message(self, fmt, *args):
        print("{} - {}".format(self.address_string(), fmt % args))

    def session(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get(COOKIE_NAME)
        if not morsel:
            return None
        record = SESSIONS.get(morsel.value)
        if not record:
            return None
        if record["expires"] < time.time():
            SESSIONS.pop(morsel.value, None)
            return None
        return record

    def new_session(self):
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        SESSIONS[token] = {"csrf": csrf, "expires": time.time() + SESSION_TTL}
        return token, csrf

    def set_session_cookie(self, token):
        value = "{}={}; HttpOnly; SameSite=Strict; Path=/; Max-Age={}".format(COOKIE_NAME, token, SESSION_TTL)
        self.send_header("Set-Cookie", value)

    def clear_session_cookie(self):
        self.send_header("Set-Cookie", "{}={}; HttpOnly; SameSite=Strict; Path=/; Max-Age=0".format(COOKIE_NAME, ""))

    def json_response(self, status, payload, cookie_token=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie_token:
            self.set_session_cookie(cookie_token)
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise ValueError("请求内容为空或过大")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            raise ValueError("请求 JSON 格式不正确")

    def require_auth(self):
        record = self.session()
        if not record:
            self.json_response(401, {"error": "请先登录"})
            return None
        return record

    def require_csrf(self, record):
        token = self.headers.get("X-CSRF-Token", "")
        if not token or not hmac.compare_digest(token, record.get("csrf", "")):
            self.json_response(403, {"error": "安全校验失败，请刷新页面后重试"})
            return False
        return True

    def serve_file(self, relative_path, root):
        try:
            target = (root / relative_path).resolve()
            root_resolved = root.resolve()
            if target != root_resolved and root_resolved not in target.parents:
                self.send_error(404)
                return
            if target.is_dir():
                target = target / "index.html"
            if not target.exists() or not target.is_file():
                self.send_error(404)
                return
            content = target.read_bytes()
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
                content_type += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_error(500)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/admin/api/"):
            self.handle_api("GET", path)
        elif path.startswith("/admin/static/"):
            self.serve_file(path[len("/admin/static/"):], ADMIN_DIR / "static")
        elif path in ("/admin", "/admin/"):
            self.serve_file("index.html", ADMIN_DIR / "static")
        elif path in ("/", "/index.html"):
            self.serve_file("index.html", SITE_DIR)
        else:
            self.serve_file(path.lstrip("/"), SITE_DIR)

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/admin/api/"):
            self.handle_api("POST", path)
        else:
            self.json_response(405, {"error": "不支持的请求"})

    def handle_api(self, method, path):
        if path == "/admin/api/status" and method == "GET":
            record = self.session()
            self.json_response(200, {
                "configured": ADMIN_FILE.exists(),
                "authenticated": bool(record),
                "csrf": record.get("csrf") if record else None,
            })
            return

        if path == "/admin/api/setup" and method == "POST":
            if ADMIN_FILE.exists():
                self.json_response(409, {"error": "管理员密码已设置"})
                return
            try:
                payload = self.read_body()
                password = str(payload.get("password", ""))
                if len(password) < 8:
                    raise ValueError("密码至少需要 8 个字符")
                salt, digest = password_hash(password)
                record = {"salt": salt, "hash": digest, "created_at": int(time.time())}
                atomic_write(ADMIN_FILE, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
                token, csrf = self.new_session()
                self.json_response(200, {"configured": True, "authenticated": True, "csrf": csrf}, token)
            except ValueError as error:
                self.json_response(400, {"error": str(error)})
            return

        if path == "/admin/api/login" and method == "POST":
            try:
                payload = self.read_body()
                password = str(payload.get("password", ""))
                record = read_json(ADMIN_FILE, {})
                if not record or not verify_password(password, record):
                    self.json_response(401, {"error": "密码不正确"})
                    return
                token, csrf = self.new_session()
                self.json_response(200, {"configured": True, "authenticated": True, "csrf": csrf}, token)
            except ValueError as error:
                self.json_response(400, {"error": str(error)})
            return

        if path == "/admin/api/logout" and method == "POST":
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            morsel = cookie.get(COOKIE_NAME)
            if morsel:
                SESSIONS.pop(morsel.value, None)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.clear_session_cookie()
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return

        record = self.require_auth()
        if not record:
            return
        if not self.require_csrf(record):
            return

        if path == "/admin/api/settings" and method == "GET":
            self.json_response(200, {"settings": load_settings()})
            return

        if path == "/admin/api/settings" and method == "POST":
            try:
                settings = clean_settings(self.read_body())
                atomic_write(SETTINGS_FILE, json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
                write_profile_data(settings)
                self.json_response(200, {"ok": True, "settings": settings})
            except ValueError as error:
                self.json_response(400, {"error": str(error)})
            return

        self.json_response(404, {"error": "接口不存在"})


def main():
    host = os.environ.get("ADMIN_HOST", "127.0.0.1")
    port = int(os.environ.get("ADMIN_PORT", "8090"))
    print("Content admin: http://{}:{}/admin".format(host, port))
    print("Public site:   http://{}:{}/".format(host, port))
    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":

    sys.exit(main())