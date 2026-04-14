# ISO2DCAT — Metadaten-Converter

Ein webbasiertes Werkzeug zur Konvertierung von Geodaten-Metadaten zwischen **ISO 19139** und **DCAT-AP** Formaten.

## Funktionen

- **ISO 19139 → DCAT-AP**: ISO 19139 XML-Metadaten in DCAT-AP RDF/XML umwandeln
- **DCAT-AP → ISO 19139**: DCAT-AP RDF/XML-Metadaten in ISO 19139 XML umwandeln

Die Konvertierung basiert auf den XSLT-Stylesheets des Projekts [inspire-dcat-de-bridge](https://code.schleswig-holstein.de/jzedlitz/inspire-dcat-de-bridge).

---

## Lokale Installation

### Voraussetzungen

- Python 3.10 oder neuer
- Git

### Schritt 1 — Repository herunterladen

```bash
git clone https://github.com/USER_NAME/iso2dcat.git
cd iso2dcat
```

### Schritt 2 — Virtuelle Umgebung erstellen und Abhängigkeiten installieren

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Schritt 3 — Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Die `.env` Datei öffnen und anpassen:

```
SECRET_KEY=ein-langer-zufaelliger-schluessel
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

Einen sicheren `SECRET_KEY` erzeugen:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Schritt 4 — Anwendung starten

```bash
python manage.py migrate
python manage.py runserver
```

Die Anwendung ist danach erreichbar unter: **http://127.0.0.1:8000**

---

## Technologie

| Komponente | Beschreibung |
|-----------|-------------|
| Django | Web-Framework |
| lxml | XSLT 1.0 Verarbeitung (ISO → DCAT) |
| saxonche | XSLT 3.0 Verarbeitung (DCAT → ISO) |
| python-dotenv | Konfiguration über Umgebungsvariablen |
