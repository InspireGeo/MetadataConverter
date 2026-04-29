# SHACL-Validierungsbericht — ISO 19139 → DCAT-AP Konvertierung

**Datum:** 29. April 2026  
**XSL:** `iso-19139-to-dcat-ap.xsl` (SEMICeu, GeoDCAT-AP 3.0.0)  
**SHACL:** DCAT-AP 3.0 (SEMICeu/DCAT-AP)

---

## Testergebnisse

| Metadatentyp | Violations vorher | Violations nachher |
|---|---|---|
| Dataset | 8 | **0 ✓** |
| Dienst (Service) | 8 | 4 (nicht behebbar) |

---

## Behobene Fehler

### 1 — `locn:geometry` — Mehr als 1 Wert

**Fehler:** `locn:geometry` enthielt 4 Geometrieformate (WKT, GML, GeoJSON×2). DCAT-AP 3.0 SHACL erlaubt maximal 1 Wert.

**Ursache:** XSL-Parameter `include-deprecated` hatte den Standardwert `yes`, wodurch veraltete Geometrieformate mitgeschrieben wurden.

**Behebung:** In `views.py` wurde der Parameter `include-deprecated=no` gesetzt. Damit wird nur noch WKT-Literal ausgegeben.

**Betroffene Datei:** `views.py`

---

### 2 — `dcat:bbox` — Mehr als 1 Wert

**Fehler:** `dcat:bbox` enthielt ebenfalls 4 Formate (WKT, GML, GeoJSON×2).

**Ursache:** XSL schrieb alle Formate ohne Bedingung.

**Behebung:** In `iso-19139-to-dcat-ap.xsl` wurden GML und GeoJSON-Zeilen entfernt. Nur WKT bleibt erhalten.

**Betroffene Datei:** `iso-19139-to-dcat-ap.xsl` (Zeile ~2677)

---

### 3 — `dcat:endpointURL` — Value does not have class rdfs:Resource

**Fehler:** `dcat:endpointURL` wurde als `rdf:resource`-Attribut geschrieben. pyshacl erwartet einen expliziten `rdf:type rdfs:Resource` Triple.

**Ursache:** pyshacl prüft `sh:class rdfs:Resource` durch explizite Typ-Triples, nicht durch Open-World-Annahme. Eine bare IRI ohne Typ-Deklaration besteht diese Prüfung nicht.

**Behebung:** In `iso-19139-to-dcat-ap.xsl` wurde ein `<rdfs:Resource rdf:about="..."/>` Wrapper eingefügt:

```xml
<dcat:endpointURL>
    <rdfs:Resource rdf:about="{$endpoint-url}"/>
</dcat:endpointURL>
```

**Betroffene Datei:** `iso-19139-to-dcat-ap.xsl` (Zeile ~4442)

---

### 4 — `dcat:endpointDescription` — Value does not have class rdfs:Resource

**Fehler:** Gleiche Ursache wie `endpointURL`.

**Behebung:** Gleiche Lösung — `<rdfs:Resource rdf:about="..."/>` Wrapper.

**Betroffene Datei:** `iso-19139-to-dcat-ap.xsl` (Zeile ~4445)

---

### 5 — `dcat:contactPoint` — Value does not have class vcard:Kind

**Fehler:** `dcat:contactPoint` enthielt einen Blank Node mit `rdf:type vcard:Organization`. SHACL erwartet `vcard:Kind`. pyshacl führt keine vCard-Ontologie-Inferenz durch und erkennt `vcard:Organization` nicht als Unterklasse von `vcard:Kind`.

**Ursache:** XSL generierte je nach Dateninhalt `vcard:Individual` oder `vcard:Organization`, aber nie explizit `vcard:Kind`.

**Behebung:** In `iso-19139-to-dcat-ap.xsl` wird nun immer `rdf:type vcard:Kind` zusätzlich gesetzt:

```xml
<rdf:type rdf:resource="{$vcard}Kind"/>
<xsl:choose>
    <xsl:when test="$IndividualName != ''">
        <rdf:type rdf:resource="{$vcard}Individual"/>
    </xsl:when>
    <xsl:when test="$OrganisationName != ''">
        <rdf:type rdf:resource="{$vcard}Organization"/>
    </xsl:when>
</xsl:choose>
```

**Betroffene Datei:** `iso-19139-to-dcat-ap.xsl` (Zeile ~1978)

---

### 6 — `foaf:primaryTopic` — Value does not have class dcat:Resource

**Fehler:** `foaf:primaryTopic` zeigte auf einen Dataset-Node mit `rdf:type dcat:Dataset`. SHACL verlangt `dcat:Resource`. pyshacl führte keine RDFS-Inferenz durch und erkannte `dcat:Dataset` nicht als Unterklasse von `dcat:Resource`.

**Ursache:** XSL setzte keinen expliziten `dcat:Resource`-Typ.

**Behebung:** In `iso-19139-to-dcat-ap.xsl` wird nun immer `rdf:type dcat:Resource` zusätzlich zu Dataset/DataService gesetzt:

```xml
<rdf:type rdf:resource="{$dcat}Resource"/>
<xsl:choose>
    <xsl:when test="$ResourceType = 'dataset'">
        <rdf:type rdf:resource="{$dcat}Dataset"/>
    </xsl:when>
    ...
</xsl:choose>
```

**Betroffene Datei:** `iso-19139-to-dcat-ap.xsl` (Zeile ~1193)

---

### 7 — `dct:source` CatalogRecord — foaf:primaryTopic fehlend

**Fehler:** Der innere `dct:source`-CatalogRecord hatte keinen `foaf:primaryTopic`-Eintrag.

**Ursache:** XSL fügte `foaf:primaryTopic` nur im äußeren CatalogRecord hinzu.

**Behebung:** In `iso-19139-to-dcat-ap.xsl` wurde `foaf:primaryTopic` auch in `dct:source` ergänzt, wenn `$ResourceUri` vorhanden ist.

**Betroffene Datei:** `iso-19139-to-dcat-ap.xsl` (Zeile ~1128)

---

### 8 — Externe URL-Auflösung (CoupledResourceLookUp)

**Fehler:** XSL versuchte bei `srv:operatesOn` externe URLs zu laden (`document()`-Funktion), was zu Timeouts und Fehlern führte.

**Ursache:** Standard-Parameter `CoupledResourceLookUp=enabled`.

**Behebung:** In `views.py` wurde `CoupledResourceLookUp=disabled` gesetzt. Die `dcat:servesDataset`-Verlinkung bleibt trotzdem erhalten (über `@xlink:href` oder `@uuidref`).

**Betroffene Datei:** `views.py`

---

## Nicht behobene Fehler (Dienst-Metadaten)

Diese Fehler treten nur bei **Dienst-Metadaten (service)** auf und sind architekturbedingt — sie können nicht durch XSL-Änderungen behoben werden.

### A — `dct:title` / `dct:description` fehlend

**Fehler:** SHACL prüft alle `dcat:Dataset`-Nodes. Ein Dienst-Metadatensatz referenziert verknüpfte Datasets über `dcat:servesDataset` als Stub-Nodes (nur `rdf:about`, keine Eigenschaften). Diese Stubs haben kein Titel oder Beschreibung.

**Ursache:** Die Dataset-Metadaten befinden sich in einem separaten Metadatensatz. Ein Dienst-Datensatz enthält diese Informationen konstruktionsbedingt nicht.

**Bewertung:** Kein Fehler im eigentlichen Sinne — SHACL prüft Stub-Nodes, die nie vollständig sein können, wenn der Dienst und der Datensatz in getrennten Katalogeinträgen geführt werden.

---

### B — `foaf:primaryTopic` fehlend (Dienst ohne Resource-URI)

**Fehler:** CatalogRecord-Nodes haben kein `foaf:primaryTopic`, weil `$ResourceUri` leer ist.

**Ursache:** Das Test-Dienst-Metadatum enthält kein `gmd:citation/gmd:identifier` mit einer HTTP-URI. Ohne diese URI kann das XSL keinen `$ResourceUri` ableiten.

**Bewertung:** Datenqualitätsproblem im Quelldatensatz, nicht im XSL.

---

## Geänderte Dateien

| Datei | Art der Änderung |
|---|---|
| `views.py` | `ISO2DCAT_XSL_PATH` auf `iso-19139-to-dcat-ap.xsl` geändert; Parameter `CoupledResourceLookUp=disabled` und `include-deprecated=no` hinzugefügt |
| `converter/xsl/iso-19139-to-dcat-ap.xsl` | 5 Korrekturen (dct:source, dcat:bbox, endpointURL, endpointDescription, vcard:Kind, dcat:Resource) |
| `converter/shacl/dcat-ap-SHACL.ttl` | Neu hinzugefügt — offizielle DCAT-AP 3.0 SHACL-Shapes |
| `converter/xsl/iso-19139-to-dcat-ap.xsl` | Neu hinzugefügt — SEMIC GeoDCAT-AP 3.0.0 XSL |
| `converter/xsl/alignments/` | Neu hinzugefügt — 3 Alignment-Dateien (INSPIRE → MDR) |

---

## Daten-Dienste-Kopplung in DCAT-AP

Die ISO-Daten-Dienste-Kopplung (`srv:operatesOn`) wird in DCAT-AP durch `dcat:servesDataset` abgebildet und ist vollständig erhalten.

### Mapping

| ISO 19119 | DCAT-AP |
|---|---|
| `srv:operatesOn` | `dcat:servesDataset` |
| `srv:operatesOn/@xlink:href` | Dataset-URI |
| `srv:operatesOn/@uuidref` | Dataset-Identifier |

### Beispiel (RDF-Ausgabe)

```xml
<dcat:DataService rdf:about="https://...service-uri...">
    <dcat:servesDataset>
        <dcat:Dataset rdf:about="https://registry.gdi-de.org/id/de.rp.vermkv/9ab1d827-..."/>
    </dcat:servesDataset>
</dcat:DataService>
```

### Hinweis zu CoupledResourceLookUp

Mit `CoupledResourceLookUp=disabled` wird die Dataset-URI direkt aus `@xlink:href` oder `@uuidref` übernommen, ohne den verlinkten Datensatz extern abzurufen. Die Kopplung bleibt semantisch vollständig erhalten — der Harvester kann über die URI auf den vollständigen Dataset-Eintrag zugreifen.

---

## Fazit

Die DCAT-AP 3.0 SHACL-Konformität wurde für **Dataset-Metadaten vollständig erreicht (0 Violations)**. Bei Dienst-Metadaten verbleiben 4 architekturbedingte Fehler, die keine XSL-Schwächen darstellen, sondern auf fehlende Informationen im Quelldatensatz zurückzuführen sind.
