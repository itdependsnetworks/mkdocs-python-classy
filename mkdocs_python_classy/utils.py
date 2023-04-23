"""Set of utility functions for the mkdocs plugin."""
import importlib
import os


def import_string(dotted_path):
    """Import a dotted module path and return the attribute/class."""
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as exc:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from exc
    module = importlib.import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as exc:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute/class') from exc


def relative_path(dest, source):
    """Get the relative path given a destination and a source."""
    if dest.split("#")[0] == source:
        return "#" + dest.split("#")[1]
    path = os.path.relpath(dest, start=source)
    return path


def get_url_from_strategy(module_path, subclass_path, urls, strategy, name):
    """Toggle what is interesting in url based on strategy and add anchor to url."""
    if strategy == "subclass":
        url = urls.get(subclass_path)
    else:
        url = urls.get(module_path)
    if url:
        return url + f"#{name.lower()}"
    return None


def verify_in_interesting_library(klass, libraries):
    """Verifty that only looking at interesting libraries."""
    if any(klass.__module__.startswith(i) for i in libraries):
        return True
    return None


def determine_klass_found(attr, elements):
    """Determine not only that a subclass was found, but which one matched."""
    for index, element in enumerate(elements):
        if issubclass(attr, (element)):
            return (index, element.__name__)
    return None


def get_dotted_path(obj):
    """Simple method to get the dotted_path given an object."""
    return obj.__module__ + "." + obj.__name__
