# Tesla Gebrauchtwagen-Watcher

Überwacht die Tesla "Sofort verfügbare Fahrzeuge"-Seite mit deinen Filtern und
schickt dir eine Push-Benachrichtigung / E-Mail bei:
- neuem Fahrzeug im Bestand
- Preisänderung an einem Fahrzeug
- Fahrzeug, das aus dem Bestand verschwindet (verkauft)

## 1. Repo einrichten

1. Erstelle ein neues **öffentliches** GitHub-Repo (wichtig: bei privaten Repos
   sind die kostenlosen GitHub-Actions-Minuten begrenzt (2.000 min/Monat) –
   bei einem Lauf alle ~15 Min. reicht das ggf. nicht. Öffentliche Repos haben
   unbegrenzte Actions-Minuten. Sensible Daten liegen nur in "Secrets", nicht
   im sichtbaren Code).
2. Lade diese Dateien hoch (oder `git push` von deinem Rechner aus):
   - `watch.py`
   - `requirements.txt`
   - `.github/workflows/watch.yml`

## 2. Die Tesla-Inventar-URL besorgen (einmalig, ~2 Min.)

1. Öffne https://www.tesla.com/de_DE/inventory/used/my im Browser.
2. Stelle **alle** Filter genau so ein, wie du sie willst (Model Y, die drei
   Allrad-Trims, Preis 29.000–37.000 €, km 10.000–51.000, Jahr 2023–2026,
   PLZ 83209).
3. Öffne die Entwicklertools (F12) → Tab **Netzwerk/Network**.
4. Gib "inventory-results" ins Filterfeld ein, ändere dann kurz irgendeinen
   Filter (z.B. Preis um 1 € verschieben und zurück), damit eine neue Anfrage
   erscheint.
5. Rechtsklick auf die Anfrage → **Copy → Copy URL**.
6. Diese komplette URL brauchst du im nächsten Schritt.

## 3. Push-Benachrichtigung einrichten (empfohlen: ntfy.sh)

1. Installiere die kostenlose App **ntfy** (iOS/Android) oder nutze den Browser.
2. Denk dir einen einzigartigen, schwer erratbaren Themennamen aus, z. B.
   `tesla-watch-<deinname>-83209-x7f2`.
3. Abonniere dieses Thema in der App ("+" → Topic eingeben).
4. Diesen Themennamen brauchst du als Secret `NTFY_TOPIC`.

*Alternative:* E-Mail per SMTP (z. B. Gmail mit App-Passwort) – dazu unten die
Secrets `EMAIL_TO`, `EMAIL_FROM`, `EMAIL_PASSWORD` setzen.

## 4. Secrets im Repo hinterlegen

Im Repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name                  | Wert                                      |
|------------------------|--------------------------------------------|
| `TESLA_INVENTORY_URL`  | die in Schritt 2 kopierte URL              |
| `NTFY_TOPIC`           | dein ntfy-Themenname (falls Push gewünscht)|
| `EMAIL_TO`             | optional, falls E-Mail gewünscht           |
| `EMAIL_FROM`           | optional                                   |
| `EMAIL_PASSWORD`       | optional (App-Passwort, nicht dein echtes) |

## 5. Aktivieren

Gehe im Repo auf den Tab **Actions** und aktiviere die Workflows (GitHub
deaktiviert geplante Workflows manchmal automatisch bei neuen Repos – einmal
"Enable workflow" klicken). Zum Testen: **Run workflow** manuell auslösen.

## Hinweise

- Das Zeitmuster 10-20-10-20 Minuten ist über den Cron-Ausdruck
  `0,10,30,40 * * * *` abgebildet (Minuten 0/10/30/40 jeder Stunde).
- GitHub-Actions-Cron ist nicht auf die Sekunde genau; bei wenig Repo-Aktivität
  kann ein Lauf ein paar Minuten später starten als geplant. Das ist normal.
- Geh nicht unter ~10 Min. Abstand – zu häufige Anfragen können von Tesla als
  Bot-Traffic geblockt werden.
- Der Zustand liegt in `state.json`, die vom Workflow nach jedem Lauf ins Repo
  zurückgeschrieben wird – so "erinnert" sich der nächste Lauf an den
  vorherigen Bestand.
