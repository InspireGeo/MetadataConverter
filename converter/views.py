from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import saxonche
import os
import io
import tempfile
import urllib.request
import urllib.error
from urllib.parse import urlparse
from pyshacl import validate as shacl_validate
from rdflib import Graph, RDF, URIRef, BNode, Namespace
from lxml import etree

XSL_DIR = os.path.join(os.path.dirname(__file__), 'xsl')
ISO2DCAT_XSL_PATH = os.path.join(XSL_DIR, 'iso-19139-to-dcat-ap.xsl')
DCAT2ISO_XSL_PATH = os.path.join(XSL_DIR, 'dcat2iso.xsl')
SHACL_PATH = os.path.join(os.path.dirname(__file__), 'shacl', 'dcat-ap-SHACL.ttl')

SH = Namespace('http://www.w3.org/ns/shacl#')


def _normalize_rdf(rdf_bytes):
    """RDF/XML'den dcat:Dataset elementini root olarak çıkarır.

    dcat2iso.xsl dcat:Dataset'in root element olmasını bekler.
    rdf:Description[rdf:type=dcat:Dataset] de dcat:Dataset'e dönüştürülür.
    """
    DCAT_NS = 'http://www.w3.org/ns/dcat#'
    RDF_NS  = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

    try:
        root = etree.fromstring(rdf_bytes)
    except etree.XMLSyntaxError:
        return rdf_bytes

    nsmap = {'rdf': RDF_NS, 'dcat': DCAT_NS}

    # rdf:Description[rdf:type=dcat:Dataset] → dcat:Dataset
    for desc in root.findall('.//rdf:Description', nsmap):
        types = desc.findall('rdf:type', nsmap)
        is_dataset = any(
            t.get(f'{{{RDF_NS}}}resource') == f'{DCAT_NS}Dataset'
            for t in types
        )
        if is_dataset:
            desc.tag = f'{{{DCAT_NS}}}Dataset'
            for t in types:
                if t.get(f'{{{RDF_NS}}}resource') == f'{DCAT_NS}Dataset':
                    desc.remove(t)

    # dcat:Dataset zaten root ise değiştirme
    if root.tag == f'{{{DCAT_NS}}}Dataset':
        return rdf_bytes

    # dcat:Dataset'i rdf:RDF içinden çıkar, root yap
    dataset = root.find(f'.//{{{DCAT_NS}}}Dataset')
    if dataset is not None:
        # rdf:RDF'deki namespace'leri Dataset'e aktar
        for prefix, uri in root.nsmap.items():
            if prefix not in dataset.nsmap:
                dataset.nsmap[prefix] = uri
        return etree.tostring(dataset, encoding='utf-8', xml_declaration=True)

    return rdf_bytes


def _short(uri):
    return str(uri).split('/')[-1].split('#')[-1] if uri else '—'


def _run_shacl(rdf_bytes):
    """RDF/XML baytlarını DCAT-AP SHACL ile doğrula. Geçen alanları da döndürür."""
    data_graph = Graph()
    data_graph.parse(io.BytesIO(rdf_bytes), format='xml')

    shacl_graph = Graph()
    shacl_graph.parse(SHACL_PATH, format='turtle')

    conforms, report_graph, _ = shacl_validate(
        io.BytesIO(rdf_bytes),
        shacl_graph=SHACL_PATH,
        data_graph_format='xml',
        shacl_graph_format='turtle',
        inference='rdfs',
        abort_on_first=False,
    )

    # Violation/warning kayıtları (focus, path_uri) anahtarıyla
    violation_map = {}
    for result in report_graph.subjects(RDF.type, SH.ValidationResult):
        severity = report_graph.value(result, SH.resultSeverity)
        focus = str(report_graph.value(result, SH.focusNode) or '')
        path = str(report_graph.value(result, SH.resultPath) or '')
        message = str(report_graph.value(result, SH.resultMessage) or '')
        value = report_graph.value(result, SH.value)

        entry = {
            'focus': focus or '—',
            'path': _short(path),
            'path_uri': path,
            'message': message,
            'value': str(value) if value else '—',
            'status': 'violation' if severity == SH.Violation else 'warning',
        }
        violation_map[(focus, path)] = entry

    # SHACL shape'lerinden targetClass → property path listesi çıkar
    class_paths = {}
    for node_shape, _, target_class in shacl_graph.triples((None, SH.targetClass, None)):
        if target_class not in class_paths:
            class_paths[target_class] = set()
        for prop_shape in shacl_graph.objects(node_shape, SH.property):
            path = shacl_graph.value(prop_shape, SH.path)
            if isinstance(path, URIRef):
                class_paths[target_class].add(str(path))

    # Geçen alanları topla
    seen = {(e['focus'], e['path_uri']) for e in violation_map.values()}
    passes = []

    for target_class, paths in class_paths.items():
        for instance in data_graph.subjects(RDF.type, target_class):
            focus = str(instance)
            for path_uri in sorted(paths):
                if (focus, path_uri) in seen:
                    continue
                seen.add((focus, path_uri))
                values = list(data_graph.objects(instance, URIRef(path_uri)))
                passes.append({
                    'focus': focus,
                    'path': _short(path_uri),
                    'path_uri': path_uri,
                    'message': '—',
                    'value': str(values[0]) if values else '(kein Wert)',
                    'status': 'pass',
                })

    violations = [e for e in violation_map.values() if e['status'] == 'violation']
    warnings = [e for e in violation_map.values() if e['status'] == 'warning']

    return conforms, violations, warnings, passes


def _fetch_url(url):
    """URL'den içerik indir, (bytes, filename) döndür."""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError('Nur HTTP/HTTPS URLs werden unterstützt.')
    req = urllib.request.Request(url, headers={'User-Agent': 'iso2dcat-converter/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read()
    filename = os.path.basename(parsed.path) or 'download'
    return content, filename


def index(request):
    return render(request, 'converter/index.html')


def validate(request):
    if request.method == 'GET':
        return render(request, 'converter/validate.html')

    uploaded_file = request.FILES.get('rdf_file')
    source_url = request.POST.get('rdf_url', '').strip()

    if not uploaded_file and not source_url:
        return render(request, 'converter/validate.html', {'error': 'Bitte eine RDF-Datei hochladen oder eine URL angeben.'})

    try:
        if source_url:
            rdf_bytes, _ = _fetch_url(source_url)
        else:
            rdf_bytes = uploaded_file.read()

        if not rdf_bytes or not rdf_bytes.strip():
            return render(request, 'converter/validate.html', {'error': 'Die Datei ist leer.'})

        conforms, violations, warnings, passes = _run_shacl(rdf_bytes)

        return render(request, 'converter/validate.html', {
            'conforms': conforms,
            'violations': violations,
            'warnings': warnings,
            'passes': passes,
            'violation_count': len(violations),
            'warning_count': len(warnings),
            'pass_count': len(passes),
        })

    except ValueError as e:
        return render(request, 'converter/validate.html', {'error': str(e)})
    except urllib.error.URLError as e:
        return render(request, 'converter/validate.html', {'error': f'URL-Fehler: {e.reason}'})
    except Exception as e:
        return render(request, 'converter/validate.html', {'error': f'Fehler: {e}'})


def iso2dcat(request):
    return render(request, 'converter/iso2dcat.html')


def dcat2iso(request):
    return render(request, 'converter/dcat2iso.html')


def convert_iso2dcat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Nur POST erlaubt.'}, status=405)

    # Kaynak: dosya veya URL
    uploaded_file = request.FILES.get('iso_file')
    source_url = request.POST.get('iso_url', '').strip()

    if not uploaded_file and not source_url:
        return render(request, 'converter/iso2dcat.html', {'error': 'Bitte eine XML-Datei hochladen oder eine URL angeben.'})

    try:
        if source_url:
            xml_content, base_name = _fetch_url(source_url)
            if not base_name.endswith('.xml'):
                base_name = base_name.split('.')[0] or 'download'
            else:
                base_name = os.path.splitext(base_name)[0]
        else:
            if not uploaded_file.name.endswith('.xml'):
                return render(request, 'converter/iso2dcat.html', {'error': 'Nur XML-Dateien werden akzeptiert.'})
            xml_content = uploaded_file.read()
            base_name = os.path.splitext(uploaded_file.name)[0]

        if not xml_content or not xml_content.strip():
            return render(request, 'converter/iso2dcat.html', {'error': 'Die Datei ist leer.'})

        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp_in:
            tmp_in.write(xml_content)
            tmp_in.flush()
            os.fsync(tmp_in.fileno())
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path + '_out.rdf'

        try:
            with saxonche.PySaxonProcessor(license=False) as proc:
                xslt_proc = proc.new_xslt30_processor()
                xslt_proc.set_cwd(XSL_DIR)
                executable = xslt_proc.compile_stylesheet(stylesheet_file=ISO2DCAT_XSL_PATH)
                executable.set_parameter('profile', proc.make_string_value('core'))
                executable.set_parameter('CoupledResourceLookUp', proc.make_string_value('disabled'))
                executable.set_parameter('include-deprecated', proc.make_string_value('no'))
                executable.transform_to_file(source_file=tmp_in_path, output_file=tmp_out_path)

            with open(tmp_out_path, 'rb') as f:
                rdf_bytes = f.read()
        finally:
            os.unlink(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)

        filename = base_name + '_dcat.rdf'
        response = HttpResponse(rdf_bytes, content_type='application/rdf+xml')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.set_cookie('fileDownload', 'true', max_age=60)
        return response

    except ValueError as e:
        return render(request, 'converter/iso2dcat.html', {'error': str(e)})
    except urllib.error.URLError as e:
        return render(request, 'converter/iso2dcat.html', {'error': f'URL-Fehler: {e.reason}'})
    except Exception as e:
        return render(request, 'converter/iso2dcat.html', {'error': f'Fehler: {e}'})


def convert_dcat2iso(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Nur POST erlaubt.'}, status=405)

    uploaded_file = request.FILES.get('dcat_file')
    source_url = request.POST.get('dcat_url', '').strip()

    if not uploaded_file and not source_url:
        return render(request, 'converter/dcat2iso.html', {'error': 'Bitte eine RDF/XML-Datei hochladen oder eine URL angeben.'})

    try:
        if source_url:
            file_content, base_name = _fetch_url(source_url)
            base_name = os.path.splitext(base_name)[0] or 'download'
        else:
            if not (uploaded_file.name.endswith('.rdf') or uploaded_file.name.endswith('.xml')):
                return render(request, 'converter/dcat2iso.html', {'error': 'Nur RDF/XML-Dateien (.rdf, .xml) werden akzeptiert.'})
            file_content = uploaded_file.read()
            base_name = os.path.splitext(uploaded_file.name)[0]

        if not file_content or not file_content.strip():
            return render(request, 'converter/dcat2iso.html', {'error': 'Die Datei ist leer.'})

        file_content = _normalize_rdf(file_content)

        with tempfile.NamedTemporaryFile(suffix='.rdf', delete=False) as tmp_in:
            tmp_in.write(file_content)
            tmp_in.flush()
            os.fsync(tmp_in.fileno())
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path + '_out.xml'

        try:
            with saxonche.PySaxonProcessor(license=False) as proc:
                xslt_proc = proc.new_xslt30_processor()
                xslt_proc.set_cwd(XSL_DIR)
                executable = xslt_proc.compile_stylesheet(stylesheet_file=DCAT2ISO_XSL_PATH)
                executable.transform_to_file(source_file=tmp_in_path, output_file=tmp_out_path)

            with open(tmp_out_path, 'rb') as f:
                xml_bytes = f.read()
        finally:
            os.unlink(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)

        filename = base_name + '_iso.xml'
        response = HttpResponse(xml_bytes, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.set_cookie('fileDownload', 'true', max_age=60)
        return response

    except ValueError as e:
        return render(request, 'converter/dcat2iso.html', {'error': str(e)})
    except urllib.error.URLError as e:
        return render(request, 'converter/dcat2iso.html', {'error': f'URL-Fehler: {e.reason}'})
    except Exception as e:
        return render(request, 'converter/dcat2iso.html', {'error': f'Fehler: {e}'})
