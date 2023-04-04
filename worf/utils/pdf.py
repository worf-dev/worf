from .email.jinja import TemplateLoader
from jinja2 import Environment, BaseLoader, TemplateNotFound
from worf.settings import settings
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
import mimetypes
import os


class URLFetcher:
    def __init__(self, paths):
        self.paths = paths

    def __call__(self, url):
        if not url.startswith("file:"):
            raise ValueError("invalid URL")
        url = url[5:]
        if url.startswith("/") or ".." in url:
            raise ValueError("illegal URL")
        for key, path in sorted(self.paths.items(), key=lambda x: x[0]):
            full_path = os.path.join(path, url)
            if not os.path.exists(full_path):
                continue
            with open(full_path, "rb") as f:
                return dict(string=f.read(), mime_type=mimetypes.guess_type(url)[0])
        raise IOError("not found")


def pdf(template_path, context, language=None):
    lang = language
    if lang is None:
        lang = settings.get("language", "en")

    def translate(key, language=None, *args, **kwargs):
        return settings.translate(language or lang, key, *args, **kwargs)

    # we set up the jinja environment with the template directories
    template_paths = settings.get("templates.paths")
    jinja_env = Environment(loader=TemplateLoader(template_paths))
    jinja_env.filters["translate"] = translate

    c = {"language": lang}

    c.update(settings.get("templates.context"))
    c.update(context)

    font_config = FontConfiguration()

    template = jinja_env.get_template(template_path)
    html = template.render(c)

    result = HTML(string=html, url_fetcher=URLFetcher(template_paths))

    return result.write_pdf()
