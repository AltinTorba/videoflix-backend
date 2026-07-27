# Videoflix Backend

Backend-API für die Videoflix-Plattform (Django + Django REST Framework), auf Basis der
Endpoint-Dokumentation und der Projekt-Checkliste der Developer Akademie.

## Stack

- Django 5 / Django REST Framework
- JWT-Authentifizierung über HttpOnly-Cookies (SimpleJWT)
- PostgreSQL als Datenbank
- Redis als Caching-Layer
- Django RQ als Background-Task-Runner (E-Mail-Versand)
- FFMPEG für die HLS-Video-Konvertierung
- Docker / Docker Compose

## Projektstruktur

```
core/              Projekt-Settings, URLs, WSGI/ASGI
authentication/     Registrierung, Login, Logout, Aktivierung, Passwort-Reset
video/              Video-Listing, HLS-Manifest & Segment-Auslieferung
```

## Setup (Docker)

1. `.env.example` nach `.env` kopieren und Werte anpassen (DB, Redis, E-Mail, Frontend-URL).
2. Container starten:

   ```bash
   docker compose up --build
   ```

3. Die API ist danach unter `http://localhost:8000/api/` erreichbar.
4. Superuser für das Admin-Panel anlegen:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

## Wichtige Endpunkte

| Methode | Endpoint | Beschreibung |
|---|---|---|
| POST | `/api/register/` | Registrierung |
| GET | `/api/activate/<uidb64>/<token>/` | Konto aktivieren |
| POST | `/api/login/` | Login (setzt HttpOnly-Cookies) |
| POST | `/api/logout/` | Logout |
| POST | `/api/token/refresh/` | Access-Token erneuern |
| POST | `/api/password_reset/` | Passwort-Reset anfordern |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Neues Passwort setzen |
| GET | `/api/video/` | Liste aller Videos |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | HLS-Manifest |
| GET | `/api/video/<id>/<resolution>/<segment>` | HLS-Segment (.ts) |

## Offene nächste Schritte

- [ ] FFMPEG-Konvertierung als RQ-Task (Upload → 480p/720p/1080p HLS-Segmente + Thumbnail)
- [ ] Signal/Post-Save-Hook auf `Video`-Modell, um die Konvertierung automatisch zu starten
- [ ] Tests für Registrierung, Login, Passwort-Reset
- [ ] Rate-Limiting/Throttling nach Bedarf
- [ ] Feintuning CORS/Cookie-Settings für Produktion (Secure, SameSite)

## Lizenz / Hinweis

Dieses Projekt ist Teil des Backend-Kurses der Developer Akademie.
