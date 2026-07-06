"""StockFlow MVP server: SQLite, tenant-scoped JSON API, sessions and live events."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import queue
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", ROOT / "stockflow.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 3000))
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in os.environ.get("FRONTEND_URL", "http://localhost:5173,http://localhost:5500,http://127.0.0.1:5500").split(",") if o.strip()]
SUBSCRIBERS: dict[str, list[queue.Queue]] = {}
SUB_LOCK = threading.Lock()


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=10000")
    return db


@contextmanager
def database():
    """Commit/rollback and always close connections to prevent SQLite lock leaks."""
    db = connect()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    with database() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS organizations (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, default_threshold INTEGER NOT NULL DEFAULT 5,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, org_id TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at INTEGER NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS products (
          id TEXT PRIMARY KEY, org_id TEXT NOT NULL, name TEXT NOT NULL, sku TEXT NOT NULL,
          description TEXT NOT NULL DEFAULT '', quantity INTEGER NOT NULL DEFAULT 0,
          cost_price REAL, selling_price REAL, low_stock_threshold INTEGER,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE,
          UNIQUE(org_id, sku)
        );
        CREATE INDEX IF NOT EXISTS idx_products_org ON products(org_id);
        """)


def uid(): return secrets.token_urlsafe(18)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split(":", 1)
        actual = hash_password(password, bytes.fromhex(salt)).split(":", 1)[1]
        return hmac.compare_digest(actual, expected)
    except ValueError:
        return False


def product_dict(row):
    return {"id": row["id"], "orgId": row["org_id"], "name": row["name"],
            "sku": row["sku"], "description": row["description"], "quantity": row["quantity"],
            "costPrice": "" if row["cost_price"] is None else row["cost_price"],
            "sellingPrice": "" if row["selling_price"] is None else row["selling_price"],
            "lowStockThreshold": "" if row["low_stock_threshold"] is None else row["low_stock_threshold"],
            "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def publish(org_id: str):
    with SUB_LOCK:
        listeners = list(SUBSCRIBERS.get(org_id, []))
    for listener in listeners:
        try: listener.put_nowait("refresh")
        except queue.Full: pass


class Handler(BaseHTTPRequestHandler):
    server_version = "StockFlow/0.1"

    def end_headers(self):
        origin = self.headers.get("Origin")
        if origin and origin.rstrip("/") in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()


    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def json_body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(size) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None

    def send_json(self, status, payload, headers=None):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(raw)

    def error_json(self, status, message): self.send_json(status, {"error": message})

    def session(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        token = jar.get("stockflow_session")
        if not token: return None
        with database() as db:
            return db.execute("""SELECT u.id user_id,u.email,u.org_id,o.name org_name,
              o.default_threshold FROM sessions s JOIN users u ON u.id=s.user_id
              JOIN organizations o ON o.id=u.org_id WHERE s.token=? AND s.expires_at>?""",
              (token.value, int(time.time()))).fetchone()

    def require_user(self):
        user = self.session()
        if not user: self.error_json(401, "Authentication required")
        return user

    def state(self, user):
        with database() as db:
            rows = db.execute("SELECT * FROM products WHERE org_id=? ORDER BY created_at DESC", (user["org_id"],)).fetchall()
        return {"user": {"id": user["user_id"], "email": user["email"], "orgId": user["org_id"]},
                "org": {"id": user["org_id"], "name": user["org_name"], "defaultThreshold": user["default_threshold"]},
                "products": [product_dict(r) for r in rows]}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self.send_json(200, {
                "service": "StockFlow API",
                "status": "OK",
                "health": "/api/health"
            })
        if path == "/api/health":
            return self.send_json(200, {"status": "OK"})
        if path == "/api":
            return self.send_json(200, {
                "service": "StockFlow API",
                "status": "OK",
                "message": "Welcome to StockFlow API",
                "health": "/api/health"
            })
        if path == "/api/session":
            user = self.session()
            return self.send_json(200, self.state(user) if user else {"user": None})
        if path == "/api/products":
            user = self.require_user()
            if not user: return
            with database() as db:
                rows = db.execute(
                    "SELECT * FROM products WHERE org_id=? ORDER BY created_at DESC",
                    (user["org_id"],)
                ).fetchall()
            return self.send_json(200, {"products": [product_dict(row) for row in rows]})
        if path == "/api/events":
            user = self.require_user()
            if not user: return
            return self.events(user["org_id"])
        return self.error_json(404, "Not found")

    def do_POST(self):
        path, data = urlparse(self.path).path, self.json_body()
        if data is None: return self.error_json(400, "Invalid JSON")
        if path == "/api/signup": return self.signup(data)
        if path == "/api/login": return self.login(data)
        if path == "/api/logout": return self.logout()
        if path == "/api/products":
            user = self.require_user()
            if user: return self.create_product(user, data)
        return self.error_json(404, "Not found")

    def do_PUT(self):
        path, data = urlparse(self.path).path, self.json_body()
        if data is None: return self.error_json(400, "Invalid JSON")
        user = self.require_user()
        if not user: return
        if path == "/api/settings": return self.settings(user, data)
        if path.startswith("/api/products/"): return self.update_product(user, path.rsplit("/", 1)[1], data)
        return self.error_json(404, "Not found")

    def do_DELETE(self):
        path = urlparse(self.path).path
        user = self.require_user()
        if not user: return
        if path.startswith("/api/products/"):
            pid = path.rsplit("/", 1)[1]
            with database() as db:
                cur = db.execute("DELETE FROM products WHERE id=? AND org_id=?", (pid, user["org_id"]))
            if not cur.rowcount: return self.error_json(404, "Product not found")
            publish(user["org_id"]); return self.send_json(200, {"ok": True})
        return self.error_json(404, "Not found")

    def signup(self, data):
        email = str(data.get("email", "")).strip().lower(); password = str(data.get("password", "")); org = str(data.get("org", "")).strip()
        if not org or "@" not in email or len(password) < 6: return self.error_json(400, "Enter an organization, valid email, and 6+ character password.")
        org_id, user_id, token = uid(), uid(), uid()
        try:
            with database() as db:
                db.execute("INSERT INTO organizations(id,name) VALUES(?,?)", (org_id, org))
                db.execute("INSERT INTO users(id,org_id,email,password_hash) VALUES(?,?,?,?)", (user_id, org_id, email, hash_password(password)))
                db.execute("INSERT INTO sessions(token,user_id,expires_at) VALUES(?,?,?)", (token, user_id, int(time.time()) + 604800))
        except sqlite3.IntegrityError: return self.error_json(409, "An account with this email already exists.")
        return self.auth_response(token)

    def login(self, data):
        email, password = str(data.get("email", "")).strip().lower(), str(data.get("password", ""))
        with database() as db: user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user or not verify_password(password, user["password_hash"]): return self.error_json(401, "Email or password is incorrect.")
        token = uid()
        with database() as db: db.execute("INSERT INTO sessions(token,user_id,expires_at) VALUES(?,?,?)", (token, user["id"], int(time.time()) + 604800))
        return self.auth_response(token)

    def auth_response(self, token):
        same_site = "None; Secure" if os.environ.get("ENV", "development") == "production" else "Lax"
        header = f"stockflow_session={token}; Path=/; HttpOnly; SameSite={same_site}; Max-Age=604800"
        jar = cookies.SimpleCookie(f"stockflow_session={token}"); token_obj = jar["stockflow_session"]
        with database() as db:
            user = db.execute("""SELECT u.id user_id,u.email,u.org_id,o.name org_name,o.default_threshold
              FROM users u JOIN organizations o ON o.id=u.org_id JOIN sessions s ON s.user_id=u.id WHERE s.token=?""", (token_obj.value,)).fetchone()
        self.send_json(200, self.state(user), {"Set-Cookie": header})

    def logout(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", "")); item = jar.get("stockflow_session")
        if item:
            with database() as db: db.execute("DELETE FROM sessions WHERE token=?", (item.value,))
        self.send_json(200, {"ok": True}, {"Set-Cookie": "stockflow_session=; Path=/; HttpOnly; Max-Age=0; SameSite=None; Secure" if os.environ.get("ENV", "development") == "production" else "stockflow_session=; Path=/; HttpOnly; Max-Age=0; SameSite=Lax"})

    def validate_product(self, d):
        name, sku = str(d.get("name", "")).strip(), str(d.get("sku", "")).strip()
        try:
            quantity = int(d.get("quantity", 0)); low = None if d.get("lowStockThreshold", "") == "" else int(d["lowStockThreshold"])
            cost = None if d.get("costPrice", "") == "" else float(d["costPrice"]); sell = None if d.get("sellingPrice", "") == "" else float(d["sellingPrice"])
        except (TypeError, ValueError): return None
        if not name or not sku or min(quantity, low if low is not None else 0) < 0 or (cost is not None and cost < 0) or (sell is not None and sell < 0): return None
        return name, sku, str(d.get("description", "")).strip(), quantity, cost, sell, low

    def create_product(self, user, data):
        values = self.validate_product(data)
        if not values: return self.error_json(400, "Check the product fields and try again.")
        pid = uid()
        try:
            with database() as db: db.execute("""INSERT INTO products(id,org_id,name,sku,description,quantity,cost_price,selling_price,low_stock_threshold)
              VALUES(?,?,?,?,?,?,?,?,?)""", (pid, user["org_id"], *values))
        except sqlite3.IntegrityError: return self.error_json(409, "SKU must be unique in your organization.")
        publish(user["org_id"]); self.send_json(201, {"id": pid})

    def update_product(self, user, pid, data):
        values = self.validate_product(data)
        if not values: return self.error_json(400, "Check the product fields and try again.")
        try:
            with database() as db:
                cur = db.execute("""UPDATE products SET name=?,sku=?,description=?,quantity=?,cost_price=?,selling_price=?,low_stock_threshold=?,updated_at=CURRENT_TIMESTAMP
                  WHERE id=? AND org_id=?""", (*values, pid, user["org_id"]))
        except sqlite3.IntegrityError: return self.error_json(409, "SKU must be unique in your organization.")
        if not cur.rowcount: return self.error_json(404, "Product not found")
        publish(user["org_id"]); self.send_json(200, {"ok": True})

    def settings(self, user, data):
        try: threshold = int(data.get("threshold"))
        except (TypeError, ValueError): return self.error_json(400, "Threshold must be a whole number.")
        if threshold < 0: return self.error_json(400, "Threshold cannot be negative.")
        with database() as db: db.execute("UPDATE organizations SET default_threshold=? WHERE id=?", (threshold, user["org_id"]))
        publish(user["org_id"]); self.send_json(200, {"ok": True})

    def events(self, org_id):
        listener = queue.Queue(maxsize=5)
        with SUB_LOCK: SUBSCRIBERS.setdefault(org_id, []).append(listener)
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.send_header("Connection", "keep-alive"); self.end_headers()
        try:
            self.wfile.write(b"event: connected\ndata: ready\n\n"); self.wfile.flush()
            while True:
                try: event = listener.get(timeout=20); message = f"event: {event}\ndata: now\n\n".encode()
                except queue.Empty: message = b": keepalive\n\n"
                self.wfile.write(message); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
        finally:
            with SUB_LOCK:
                if listener in SUBSCRIBERS.get(org_id, []): SUBSCRIBERS[org_id].remove(listener)

if __name__ == "__main__":
    init_db()
    print(f"StockFlow running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
