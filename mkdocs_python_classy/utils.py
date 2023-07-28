"""Set of utility functions for the mkdocs plugin."""
import ast
import importlib
import inspect
import os
import sys
import types

if sys.version_info < (3, 9):
    # ast.unparse only supported as of 3.9
    import astunparse

    def _unparse(val):
        """Required since astunparse has an extra newline compared to ast.unparse."""
        return astunparse.unparse(val).rstrip()

    ast.unparse = _unparse


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
    """Function that gets the actual code via ast of the class attributes."""

    class StopTreeTraversal(Exception):
        """Custom exception to stop tree traversal."""

    class ClassAttributeVisitor(ast.NodeVisitor):
        """Overwrite the ast class, to only check the `visit_Assign` method."""

        def __init__(self):
            """Initialiaze the class and assign variables."""
            self.class_attributes = {}
            self.class_members = [name for name, _ in _getmembers_static(cls)]

        def visit_Assign(self, node):  # pylint: disable=invalid-name
            """Method that we care to overwrite, looking to ensure only looking at assignment on the class."""
            # Once all of the class attributes have been exhausted, we don't need to
            # continute with the walk any further
            if not self.class_members:
                raise StopTreeTraversal()
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    # This is an instance attribute, not a class attribute
                    pass
                else:
                    if isinstance(target, ast.Name) and target.id in self.class_members:
                        attr_name = target.id
                        attr_code = ast.unparse(node.value)
                        self.class_attributes[attr_name] = attr_code
                        self.class_members.remove(attr_name)

    source_code = inspect.getsource(cls)
    tree = ast.parse(source_code)
    try:
        visitor = ClassAttributeVisitor()
        visitor.visit(tree)
    except StopTreeTraversal:
        pass
    return visitor.class_attributes


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


def _getmembers_static(object, predicate=None):  # pylint: disable=redefined-builtin,too-many-branches
    """This is a vendored approach to _getmembers_static that came in py3.11."""
    if inspect.isclass(object):
        mro = (object,) + inspect.getmro(object)
    else:
        mro = ()
    results = []
    processed = set()
    names = dir(object)
    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists
    try:
        for base in object.__bases__:
            for key, val in base.__dict__.items():
                if isinstance(val, types.DynamicClassAttribute):
                    names.append(key)
    except AttributeError:
        pass
    for key in names:
        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        try:
            value = inspect.getattr_static(object, key)
            # handle the duplicate key
            if key in processed:
                raise AttributeError
        except AttributeError:
            for base in mro:
                if key in base.__dict__:
                    value = base.__dict__[key]
                    break
            else:
                # could be a (currently) missing slot member, or a buggy
                # __dir__; discard and move on
                continue
        if not predicate or predicate(value):
            results.append((key, value))
        processed.add(key)
    results.sort(key=lambda pair: pair[0])
    return results
