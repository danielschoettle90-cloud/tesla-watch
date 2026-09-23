import os
import json
import hashlib
import requests
from datetime import datetime, timezone

STATE_FILE = "state.json"

# --- Konfiguration ---
# So bekommst du die richtige URL (1x einmalig, dauert 2 Minuten):
# 1. Öffne https://www.tesla.com/de_DE/inventory/used/my im Browser
# 2. Stelle ALLE Filter genau so ein wie im Screenshot (Model Y, Trims, Preis, km, Jahr, PLZ)
# 3. Öffne die DevTools (F12) -> Tab "Netzwerk" / "Network"
# 4. Filtere nach "inventory-results", lade die Seite neu (oder ändere kurz einen Filter)
# 5. Rechtsklick auf die Anfrage -> "Copy" -> "Copy URL"
# 6. Diese URL als TESLA_INVENTORY_URL setzen (unten als Environment-Variable / GitHub Secret)
INVENTORY_URL = os.environ.get("TESLA_INVENTORY_URL", "PASTE_YOUR_COPIED_URL_HERE")

# Push-Benachrichtigung über ntfy.sh (App im Play/App Store: "ntfy")
# Wähle einen einzigartigen, schwer zu erratenden Topic-Namen, z.B. "tesla-watch-maxmustermann-83209"
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")

# Alternativ/zusätzlich: E-Mail per SMTP (z.B. Gmail mit App-Passwort)
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Referer": "https://www.tesla.com/de_DE/inventory/used/my",
    "Origin": "https://www.tesla.com",
    "x-requested-with": "XMLHttpRequest",
}


def fetch_inventory():
    resp = requests.get(INVENTORY_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])

    vehicles = {}
    for v in results:
        vin = v.get("VIN") or v.get("Vin") or hashlib.md5(
            json.dumps(v, sort_keys=True).encode()
        ).hexdigest()
        vehicles[vin] = {
            "price": v.get("Price") or v.get("TotalPrice"),
            "trim": v.get("TrimName", ""),
            "year": v.get("Year"),
            "km": v.get("Odometer"),
            "city": (v.get("VehicleAddress") or {}).get("City", ""),
        }
    return vehicles


def load_previous_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(vehicles):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(vehicles, f, ensure_ascii=False, indent=2)


def diff(old, new):
    messages = []
    old_vins, new_vins = set(old), set(new)

    for vin in new_vins - old_vins:
        v = new[vin]
        messages.append(
            f"🆕 Neues Fahrzeug: {v['trim']} {v['year']} – {v['price']} € – "
            f"{v['km']} km – {v['city']} – VIN ...{vin[-6:]}"
        )

    for vin in old_vins - new_vins:
        v = old[vin]
        messages.append(
            f"❌ Nicht mehr verfügbar: {v['trim']} {v['year']} – {v['price']} € – VIN ...{vin[-6:]}"
        )

    for vin in old_vins & new_vins:
        if old[vin]["price"] != new[vin]["price"]:
            v = new[vin]
            messages.append(
                f"💶 Preisänderung: {v['trim']} {v['year']} – "
                f"{old[vin]['price']} € → {v['price']} € – VIN ...{vin[-6:]}"
            )
    return messages


def notify(messages):
    if not messages:
        return
    text = "\n".join(messages)
    print(text)

    if NTFY_TOPIC:
        try:
            requests.post(
                f"https://ntfy.sh/{NTFY_TOPIC}",
                data=text.encode("utf-8"),
                headers={"Title": "Tesla Inventar-Update", "Priority": "high"},
                timeout=10,
            )
        except Exception as e:
            print("ntfy Fehler:", e)

    if EMAIL_TO and EMAIL_FROM and EMAIL_PASSWORD:
        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(text, "plain", "utf-8")
            msg["Subject"] = "Tesla Inventar-Update"
            msg["From"] = EMAIL_FROM
            msg["To"] = EMAIL_TO
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        except Exception as e:
            print("E-Mail Fehler:", e)


def main():
    if INVENTORY_URL == "PASTE_YOUR_COPIED_URL_HERE":
        raise SystemExit(
            "Bitte TESLA_INVENTORY_URL setzen (siehe Kommentar im Skript / README)."
        )

    new_state = fetch_inventory()
    old_state = load_previous_state()
    changes = diff(old_state, new_state)
    notify(changes)
    save_state(new_state)

    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {len(new_state)} Fahrzeuge geprüft, {len(changes)} Änderungen.")


if __name__ == "__main__":
    main()
