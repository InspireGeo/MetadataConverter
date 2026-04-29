# ISO 19139 ↔ DCAT-AP Mapping

Mapping-Tabelle basierend auf den XSLT-Stylesheets `iso2dcat.xsl` und `dcat2iso.xsl`.

---

## Kern-Metadaten

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:fileIdentifier` | `dct:identifier` + `adms:identifier` | |
| `gmd:dateStamp` | `dct:modified` | Metadaten-Datum |
| `gmd:language` | `dct:language` | 3-Zeichen-Code (ISO 639-2) |
| `gmd:characterSet` | `cnt:characterEncoding` | Nur im Extended-Modus |
| `gmd:hierarchyLevel` (dataset/series) | `dct:type` | INSPIRE ResourceType URI |
| `gmd:hierarchyLevel` (service) | `dct:type` | INSPIRE SpatialDataServiceType |
| `gmd:parentIdentifier` | — | **Kein DCAT-Äquivalent** |
| `gmd:metadataStandardName/Version` | `dct:source / dct:conformsTo` | Nur im Extended-Modus |

---

## Identifikation

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:citation/gmd:title` | `dct:title` | Mehrsprachig via PT_FreeText |
| `gmd:abstract` | `dct:description` | Mehrsprachig via PT_FreeText |
| `gmd:citation/gmd:identifier/gmd:code` | `dct:identifier` | Ressourcen-Identifier |
| `gmd:resourceMaintenance/.../gmd:maintenanceAndUpdateFrequency` | `dct:accrualPeriodicity` | |

---

## Datumsangaben

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:date` (dateType = publication) | `dct:issued` | |
| `gmd:date` (dateType = revision) | `dct:modified` | |
| `gmd:date` (dateType = creation) | `dct:created` | |

---

## Verantwortliche Stellen

| ISO 19139 Rolle (`CI_RoleCode`) | DCAT-AP Element | RDF-Typ |
|---|---|---|
| `pointOfContact` | `dcat:contactPoint` | `vcard:Organization` / `vcard:Individual` |
| `publisher`, `author` | `dct:publisher` | `foaf:Organization` |
| `originator` | `dct:creator` | `foaf:Organization` |
| `owner` | `dct:rightsHolder` | `foaf:Organization` |
| `custodian` | `dcatde:maintainer` | `foaf:Organization` |

Kontaktdetails:

| ISO 19139 Element | DCAT-AP Element |
|---|---|
| `gmd:organisationName` | `foaf:name` / `vcard:organization-name` |
| `gmd:individualName` | `foaf:name` / `vcard:fn` |
| `gmd:electronicMailAddress` | `foaf:mbox` / `vcard:hasEmail` |
| `gmd:voice` (Telefon) | `foaf:phone` / `vcard:hasTelephone` |
| `gmd:onlineResource/gmd:linkage` | `foaf:homepage` / `vcard:hasURL` |
| `gmd:deliveryPoint` | `locn:thoroughfare` / `vcard:street-address` |
| `gmd:city` | `locn:postName` / `vcard:locality` |
| `gmd:postalCode` | `locn:postCode` / `vcard:postal-code` |
| `gmd:administrativeArea` | `locn:adminUnitL2` / `vcard:region` |
| `gmd:country` | `locn:adminUnitL1` / `vcard:country-name` |

---

## Schlüsselwörter & Themen

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:descriptiveKeywords/gmd:keyword` | `dcat:keyword` | Freie Schlagworte |
| GEMET INSPIRE-Themes Schlagwort | `dcat:theme` | URI aus INSPIRE Themes |
| `gmd:topicCategory` | `dcat:theme` | Mapping auf EU MDR Data Themes |
| `gmd:topicCategory` (NRW-Modus) | `dcat:theme` | Open.NRW-spezifisch |

Themen-Mapping (`gmd:topicCategory` → `dcat:theme`):

| ISO topicCategory | DCAT EU MDR Theme |
|---|---|
| farming | AGRI |
| economy | ECON |
| society | EDUC, SOCI |
| utilitiesCommunication | ENER |
| environment, biota, climatology, geoscientific, inlandWaters, oceans, imagery | ENVI |
| health | HEAL |
| intelligenceMilitary | JUST |
| location, boundaries, planningCadastre, structure | REGI |
| transportation | TRAN |

---

## Räumliche Ausdehnung

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:EX_GeographicBoundingBox` | `dct:spatial / dct:Location / locn:geometry` | GML + WKT Literal |
| `gmd:EX_GeographicDescription` | `rdfs:seeAlso / skos:Concept` | Standard-Modus |
| `gmd:EX_GeographicDescription` | `dcatde:politicalGeocodingLevelURI` | NRW-Modus |
| `dcatde:politicalGeocodingURI` | `gmd:EX_GeographicDescription` | (Rückrichtung) |
| `gmd:MD_Resolution` (Maßstab) | — | **Kein DCAT-Äquivalent** |

---

## Zeitliche Ausdehnung

| ISO 19139 Element | DCAT-AP Element |
|---|---|
| `gml:TimePeriod / gml:beginPosition` | `dct:temporal / schema:startDate` |
| `gml:TimePeriod / gml:endPosition` | `dct:temporal / schema:endDate` |

---

## Nutzungsbedingungen & Lizenzen

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:resourceConstraints / gmd:otherConstraints` (otherRestrictions) | `dct:accessRights` | |
| `gmd:resourceConstraints / gmd:MD_LegalConstraints` | `dct:license` | Distribution-Ebene |

---

## Distribution & Dienste

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:distributionInfo / gmd:MD_Format` | `dcat:distribution / dct:format` | |
| `gmd:onLine/gmd:linkage` (download) | `dcat:distribution / dcat:downloadURL` | |
| `gmd:onLine/gmd:linkage` (information) | `dcat:distribution / foaf:page` | |
| `gmd:onLine/gmd:linkage` (allgemein) | `dcat:distribution / dcat:accessURL` | |
| `dcat:landingPage` | `gmd:onLine` (CI_OnLineFunctionCode: information) | Rückrichtung: kein dediziertes ISO-Feld |

### Dienste (service hierarchyLevel)

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `srv:serviceType` (WMS, VIEW) | `dct:type` → SpatialDataServiceType/view | |
| `srv:serviceType` (WFS, WCS, download) | `dct:type` → SpatialDataServiceType/download | |
| `srv:serviceType` (CSW, discovery) | `dct:type` → SpatialDataServiceType/discovery | |
| `srv:serviceType` (WPS, transformation) | `dct:type` → SpatialDataServiceType/transformation | |
| `srv:containsOperations` (GetCapabilities URL) | `dcat:accessURL` | |
| `srv:operatesOn` | — | **Kein DCAT-Äquivalent — Daten-Dienste-Kopplung nicht abgebildet** |

---

## Datenqualität & Konformität

| ISO 19139 Element | DCAT-AP Element | Hinweis |
|---|---|---|
| `gmd:dataQualityInfo / gmd:lineage / gmd:statement` | `dct:provenance` | |
| `gmd:DQ_ConformanceResult / gmd:specification` | `dct:conformsTo` | Nur bei pass=true |
| `gmd:DQ_ConformanceResult` | `wdrs:describedby / earl:Assertion` | Nur im Extended-Modus |

---

## Nicht gemappte / Problematische Felder

| ISO 19139 Element | Problem |
|---|---|
| `srv:operatesOn` | Daten-Dienste-Kopplung: kein DCAT-Äquivalent. `dcat:servesDataset` wäre die korrekte Entsprechung, ist aber im Mapping nicht implementiert. |
| `gmd:MD_Resolution` | Maßstab / Bodenauflösung: kein DCAT-Äquivalent |
| `gmd:parentIdentifier` | Hierarchie-Beziehungen: kein DCAT-Äquivalent |
| `dcat:landingPage` | Kein dediziertes ISO-Feld; wird als `gmd:onLine` (information) gemappt |
| `gmd:topicCategory` | Mapping auf EU MDR Themes ist nur annähernd; 1:n-Beziehung bei ENVI und REGI |
| `gmd:metadataStandardName/Version` | Nur im Extended-Modus (nicht Standard-DCAT-AP) |
| `gmd:characterSet` | Nur im Extended-Modus |
| `dcatde:politicalGeocodingLevelURI` vs `dcatde:politicalGeocodingURI` | Unterschiedliche Semantik; Rückrichtung nur für `politicalGeocodingURI` implementiert |
