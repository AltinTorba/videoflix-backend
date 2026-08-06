# Videoflix Backend

Backend-API für die Videoflix-Plattform (Django + Django REST Framework), auf Basis der
Endpoint-Dokumentation und der Projekt-Checkliste der Developer Akademie.

## Stack

- Django 5 / Django REST Framework
- JWT-Authentifizierung über HttpOnly-Cookies (SimpleJWT)
- PostgreSQL als Datenbank
- Redis als Caching-Layer (django-redis) **und** als Broker für Django RQ
- Django RQ als Background-Task-Runner (E-Mail-Versand, Video-Konvertierung)
- FFMPEG für die HLS-Video-Konvertierung (480p / 720p / 1080p)
- WhiteNoise für das Ausliefern statischer Dateien (Admin-Panel) über Gunicorn
- Docker / Docker Compose

## Projektstruktur

```
core/                Projekt-Settings, URLs, WSGI/ASGI
authentication/       Registrierung, Login, Logout, Aktivierung, Passwort-Reset
  authentication.py   Liest den JWT-Access-Token aus dem HttpOnly-Cookie
  functions.py        Hilfsfunktionen: Aktivierungs-/Reset-Links, Cookie-Handling
  tasks.py            Django-RQ-Jobs für den E-Mail-Versand
  views.py            Nur Views, die eine Response zurückgeben
video/                 Video-Listing, HLS-Manifest- und Segment-Auslieferung
  models.py           Video-Modell inkl. Status-Tracking (pending/processing/ready/failed)
  converters.py       Baut und startet die FFMPEG-Kommandos für HLS + Thumbnail
  tasks.py            Django-RQ-Job: konvertiert eine Video-Datei in alle Auflösungen
  signals.py          Startet die Konvertierung automatisch bei neuem Video, invalidiert Cache
  views.py            Video-Liste (mit Redis-Cache) + HLS-Manifest/Segment-Auslieferung
entrypoint.sh          Wartet auf die DB, migriert, sammelt Static Files, startet Gunicorn (web)
entrypoint-worker.sh   Wartet auf die DB, startet den RQ-Worker (kein migrate, verhindert Race Condition)
```

## Setup (Docker)

1. `.env.example` nach `.env` kopieren und Werte anpassen:
   ```bash
   cp .env.example .env
   ```
   Wichtige Variablen:
   - `SECRET_KEY` — mit `python -c "import secrets; print(secrets.token_urlsafe(50))"` generieren
   - `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — z. B. ein Gmail-App-Passwort für echten E-Mail-Versand
   - `FRONTEND_URL` — Basis-URL des Frontends (wird für Aktivierungs-/Reset-Links und CORS verwendet,
     z. B. `http://127.0.0.1:5500` bei VS-Code Live Server)

2. Container bauen und starten:
   ```bash
   docker compose up --build
   ```
   Das startet vier Container: `db` (Postgres), `redis`, `web` (Gunicorn, Port 8080 → 8000),
   `rqworker` (Django RQ). Migrationen werden beim Start von `web` automatisch angewendet.

3. Superuser für das Admin-Panel anlegen:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
   Admin-Panel: `http://localhost:8080/admin/`

4. Video hinzufügen: im Admin-Panel unter **Videos → Add Video** eine Quelldatei (`source_file`)
   hochladen. Die HLS-Konvertierung (480p/720p/1080p) sowie das Thumbnail werden automatisch im
   Hintergrund per Django RQ erstellt (Fortschritt im Log von `rqworker` sichtbar).

## API-Endpunkte

| Methode | Endpoint | Beschreibung |
|---|---|---|
| POST | `/api/register/` | Registrierung |
| GET | `/api/activate/<uidb64>/<token>/` | Konto aktivieren |
| POST | `/api/login/` | Login (setzt HttpOnly-Cookies) |
| POST | `/api/logout/` | Logout (löscht Cookies, blacklisted Refresh-Token) |
| POST | `/api/token/refresh/` | Access-Token erneuern |
| POST | `/api/password_reset/` | Passwort-Reset anfordern |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Neues Passwort setzen |
| GET | `/api/video/` | Liste aller Videos (Redis-gecacht) |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | HLS-Manifest |
| GET | `/api/video/<id>/<resolution>/<segment>` | HLS-Segment (.ts) |

Alle Video-Endpunkte erfordern JWT-Authentifizierung über das `access_token`-Cookie.

## Video-Verarbeitung & Fehlerbehandlung

Jedes `Video`-Objekt hat ein `status`-Feld (`pending` → `processing` → `ready`/`failed`) sowie
`processing_error` für Diagnosezwecke. Schlägt die FFMPEG-Konvertierung fehl (z. B. beschädigte
Datei), wird der Fehler abgefangen, der Status auf `failed` gesetzt und die Fehlermeldung
gespeichert — sichtbar im Admin-Panel.

## Getestet

- Vollständiger Auth-Flow (Register → E-Mail → Aktivierung → Login → Logout → Token-Refresh →
  Passwort-Reset) über `curl` **und** über das offizielle Vanilla-JS-Frontend
  ([project.Videoflix](https://github.com/Developer-Akademie-Backendkurs/project.Videoflix))
- HLS-Konvertierung mit Test-Videos (Kurzvideo für Basistest, 60-Sekunden-Video zur Verifizierung
  der Mehrfach-Segmentierung: 8 Segmente × 3 Auflösungen)
- Redis-Cache für die Video-Liste (verifiziert über `redis-cli -n 1 KEYS "*"`)
- `docker compose down -v && docker compose up --build` (vollständiger Neustart ohne manuelle
  Zwischenschritte)
- `flake8` (PEP-8) ohne Verstöße

## Lizenz / Hinweis

Dieses Projekt ist Teil des Backend-Kurses der Developer Akademie.
