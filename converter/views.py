from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from lxml import etree
import saxonche
import os
import tempfile
import urllib.request
import urllib.error
from urllib.parse import urlparse

XSL_DIR = os.path.join(os.path.dirname(__file__), 'xsl')
XSL_PATH = os.path.join(XSL_DIR, 'iso2dcat.xsl')
DCAT2ISO_XSL_PATH = os.path.join(XSL_DIR, 'dcat2iso.xsl')


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

        xml_doc = etree.fromstring(xml_content)

        prev_dir = os.getcwd()
        os.chdir(XSL_DIR)
        try:
            xsl_doc = etree.parse('iso2dcat.xsl')
            transform = etree.XSLT(xsl_doc)
            result = transform(xml_doc)
        finally:
            os.chdir(prev_dir)

        rdf_bytes = etree.tostring(result, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        filename = base_name + '_dcat.rdf'
        response = HttpResponse(rdf_bytes, content_type='application/rdf+xml')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.set_cookie('fileDownload', 'true', max_age=60)
        return response

    except ValueError as e:
        return render(request, 'converter/iso2dcat.html', {'error': str(e)})
    except urllib.error.URLError as e:
        return render(request, 'converter/iso2dcat.html', {'error': f'URL-Fehler: {e.reason}'})
    except etree.XMLSyntaxError as e:
        return render(request, 'converter/iso2dcat.html', {'error': f'XML-Fehler: {e}'})
    except etree.XSLTError as e:
        return render(request, 'converter/iso2dcat.html', {'error': f'XSLT-Fehler: {e}'})
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

        with tempfile.NamedTemporaryFile(suffix='.rdf', delete=False) as tmp_in:
            tmp_in.write(file_content)
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path + '_out.xml'

        try:
            with saxonche.PySaxonProcessor(license=False) as proc:
                xslt_proc = proc.new_xslt30_processor()
                xslt_proc.set_cwd(XSL_DIR)
                executable = xslt_proc.compile_stylesheet(stylesheet_file=DCAT2ISO_XSL_PATH)
                executable.set_initial_match_selection(file_name=tmp_in_path)
                executable.apply_templates_returning_file(output_file=tmp_out_path)

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
