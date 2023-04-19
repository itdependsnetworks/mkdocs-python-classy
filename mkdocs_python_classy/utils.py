import importlib
import os


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError:
        raise ImportError("%s doesn't look like a module path" % dotted_path)
    module = importlib.import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (module_path, class_name))


def relative_path(dest, source):
    """Get the relative path given a destination and a source."""
    return os.path.relpath(dest, start=source + "/")


def get_url_from_strategy(module_path, subclass_path, urls, strategy, name):
    if strategy == "subclass":
        url = urls.get(subclass_path)
    else:
        url = urls.get(module_path)
    if url:
        return url + f"#{name.lower()}"


def verify_in_interesting_library(klass, libraries):
    if any([klass.__module__.startswith(i) for i in libraries]):
        return True


def determine_klass_found(attr, elements):
    for index, element in enumerate(elements):
        if issubclass(attr, (element)):
            return (index, element.__name__)


def dotted_path(obj):
    return obj.__module__ + "." + obj.__name__
