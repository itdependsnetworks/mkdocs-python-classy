"""Set of utility functions for the mkdocs plugin."""
import ast
import importlib
import inspect
import os


def determine_klass_found(attr, elements):
    """Determine not only that a subclass was found, but which one matched."""
    for index, element in enumerate(elements):
        if issubclass(attr, (element)):
            return (index, element.__name__)
    return None


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


def is_function_attribute(cls, attr_name):
    """Function to verity whther or not an `attr` is a function/method or not."""
    source_code = inspect.getsource(cls)
    tree = ast.parse(source_code)

    # Define a custom visitor to traverse the AST
    class FunctionCheckVisitor(ast.NodeVisitor):
        """Overwrite AST class to only check if code is a function."""

        def __init__(self):
            """Set to False to start."""
            self.is_function_attr = False

        def visit_Assign(self, node):  # pylint: disable=invalid-name
            """Overwrite ast method."""
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == attr_name:
                    self.is_function_attr = isinstance(node.value, ast.FunctionDef)
                    return

    # Create an instance of the custom visitor
    visitor = FunctionCheckVisitor()

    # Visit the AST
    visitor.visit(tree)

    return visitor.is_function_attr


def get_attribute_code(cls):
    """Function to get the actual code of each attribute."""
    my_dict = {}
    source_code = inspect.getsource(cls)
    tree = ast.parse(source_code)
    inside_class = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            inside_class = True
        elif isinstance(node, ast.FunctionDef):
            inside_class = False
        if inside_class and isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
                    attr_name = target.id
                    attr_code = ast.unparse(node.value)
                    my_dict[attr_name] = attr_code
    return my_dict


def get_dotted_path(obj):
    """Simple method to get the dotted_path given an object."""
    return obj.__module__ + "." + obj.__name__


def get_url_from_strategy(module_path, subclass_path, urls, strategy, name):
    """Toggle what is interesting in url based on strategy and add anchor to url."""
    if strategy == "subclass":
        url = urls.get(subclass_path)
    else:
        url = urls.get(module_path)
    if url:
        return url + f"#{name.lower()}"
    return None


def relative_path(dest, source):
    """Get the relative path given a destination and a source."""
    if dest.split("#")[0] == source:
        return "#" + dest.split("#")[1]
    path = os.path.relpath(dest, start=source)
    return path


def verify_in_interesting_library(klass, libraries):
    """Verifty that only looking at interesting libraries."""
    if any(klass.__module__.startswith(i) for i in libraries):
        return True
    return None
