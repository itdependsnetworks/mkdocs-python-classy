"""mkdocs-python-classy plugin for MkDocs."""
import re
from string import Template
from importlib_metadata import version

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.config import Config
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdocs_python_classy.utils import dotted_path, relative_path
from mkdocs_python_classy.inspector import InspectorGeneral
from mkdocs_python_classy.constants import EXTRA_CSS, TEMPLATE_STRING

__version__ = version(__package__)


class MkDocsPythonClassyPlugin(BasePlugin):
    """MkDocs plugin entry point for mkdocs-python-classy."""

    config_scheme = (
        ("classy_strategy", config_options.Choice(tuple(["subclass", "module"]), default="subclass")),
        ("classy_subclasses", config_options.ListOfItems(config_options.Type(str))),
        ("classy_modules", config_options.ListOfItems(config_options.Type(str))),
        ("classy_libraries", config_options.ListOfItems(config_options.Type(str))),
    )
    inspector = None

    def on_nav(self, nav, config, files):
        urls = {}
        for page in nav.pages:
            with open(page.file.abs_src_path) as f:
                first_line = f.readline()
                if first_line.startswith(";;; "):
                    dotted_string = first_line.splitlines()[0][4:]
                    # TODO: verify path is good here
                    urls[dotted_string] = "/" + page.url

        strategy = self.config["classy_strategy"]
        subclasses = self.config["classy_subclasses"] if strategy == "module" else list(urls.keys())
        modules = self.config["classy_modules"] if strategy == "subclass" else list(urls.keys())
        self.inspector = InspectorGeneral(
            self.config["classy_strategy"], subclasses, modules, urls, self.config["classy_libraries"]
        )
        return nav

    def on_page_markdown(self, markdown: str, page: Page, config: Config, files: Files) -> str:
        """
        Called on each file after it is read and before it is converted to HTML.
        """
        if not markdown.startswith(";;;"):
            return markdown
        module = markdown.splitlines()[0][4:]

        output = f"# `{module}` Found Classes"
        render_each = []
        for name, value in self.inspector.klasses.items():
            if value["subclass_path"] == module:
                render_each.append(name)
        for item in sorted(render_each):
            output = output + self.get_context(item)
        return output

    def on_page_content(self, html: str, page: Page, config: Config, files: Files) -> str:
        if re.search("CLASSY_DELIMITER", html):
            html = re.sub("CLASSY_DELIMITER (\\S+)", r'<small class="pull-right">\1</small>', html)
            html = html + EXTRA_CSS
        return html

    def get_context(self, name):
        context = {}
        inspect_obj = self.inspector.klass_details[name]

        def _ancestors(ancestors, urls, current_url, path_short_map):
            _out = f"1. {ancestors[0].__name__}\n"

            for ancestor in ancestors[1:]:
                name = ancestor.__name__
                module_path = dotted_path(ancestor)
                if urls.get(module_path):
                    path = relative_path(urls[module_path]["url"], current_url)
                    _out += f"1. [{name}]({path})\n"
                elif urls.get(path_short_map.get(ancestor.__name__)):
                    path = relative_path(urls[path_short_map[ancestor.__name__]]["url"], current_url)
                    _out += f"1. [{name}]({path})\n"
                else:
                    _out += f"1. {name}\n"
            return _out

        def _descendants(descendants, urls, current_url, name):
            if not descendants:
                return ""
            _out = f"The below Classes rely on: `{name}`.\n\n"
            for descendant in descendants:
                module_path = dotted_path(descendant)
                _out += f"- [{descendant.__name__}]({relative_path(urls[module_path]['url'], current_url)})\n"
            return _out

        def _attributes(attributes):
            if not attributes:
                return "No attributes in `{{ this_module }}.{{ name }}`"
            _out = "| Key | Value | Defined in |\n"
            _out += "| :-- | :---- | :--------- |\n"
            previous_name = None
            for attribute in attributes:
                name = attribute.name
                if previous_name == attribute.name:
                    name = f"~~{name}~~"
                _out += f"{name} | `{attribute.repr_value}` | {attribute.classobject.__name__ } |\n"
                previous_name = attribute.name

            return _out

        def _methods(methods):
            _out = ""
            for method in methods:
                _out += f"""??? quote "`def {method.name}({method.params_string()}):` CLASSY_DELIMITER {method.classobject.__name__ }"\n"""
                _out += "    \n"
                children = [method] + method.children
                for child in children:
                    if len(children) != 1:
                        _out += "    \n"
                        _out += f"    **{child.classobject.__name__}**\n"
                    _out += "    \n"
                    _out += f'    ``` py linenums="{child.line_number()}"\n'
                    _out += "    \n"
                    for line in child.code().splitlines():
                        _out += f"    {line}\n"
                    _out += "    ```\n"
                _out += "\n"
            return _out

        current_url = self.inspector.klasses[name]["url"].split("#")[0]
        context["name"] = name.split(".")[-1]
        context["import_statment"] = f"from {name.rsplit('.', 1)[0]} import {name.rsplit('.', 1)[1]}"
        context["ancestors"] = _ancestors(
            inspect_obj.get_klass_mro(), self.inspector.klasses, current_url, self.inspector.klass_short
        )
        context["descendants"] = _descendants(
            inspect_obj.get_children(), self.inspector.klasses, current_url, context["name"]
        )
        context["attributes"] = _attributes(inspect_obj.get_attributes())
        context["methods"] = _methods(inspect_obj.get_methods())
        return Template(TEMPLATE_STRING).substitute(**context)
