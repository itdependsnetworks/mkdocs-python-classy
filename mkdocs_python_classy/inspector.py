"""Module to handle all inspection related tasks."""
import collections
import importlib
import inspect
import types

from pygments import lex
from pygments.lexers import PythonLexer  # pylint: disable=no-name-in-module
from pygments.token import Token

from mkdocs_python_classy.utils import import_string, get_dotted_path, get_attribute_code, is_function_attribute


class Attribute:
    """Class object to inepct attributes."""

    def __init__(self, name, value, classobject, instance_class, attr_code):  # pylint: disable=too-many-arguments
        """Initialize the Class.

        Args:
            name (str): The name of the attribute.
            value (obj): The value of the attribute.
            classobject (obj): The class where the Attribute came from.
            instance_class (obj): The class instance where the Attribute came from.
            attr_code (str): The code as parsed via ast.
        """
        self.name = name
        self.value = value
        self.classobject = classobject
        self.instance_class = instance_class
        self.dirty = False
        self.attr_code = attr_code

    @property
    def repr_value(self):
        """Convert to repr value which is more human readable."""
        return repr(self.value)

    def __eq__(self, obj):
        """Overwrite equality to ensure that name and value are the same only."""
        return self.name == obj.name and self.value == obj.value

    def __neq__(self, obj):
        """Overwrite inequality to ensure that name and value are the same only."""
        return not self.__eq__(obj)


class Method(Attribute):
    """Class object to inepct methods."""

    def __init__(self, *args, **kwargs):
        """Add children to method."""
        super().__init__(*args, **kwargs)
        self.children = []

    def params_string(self):
        """Get the string value of the parameters."""
        stack = []
        argspec = inspect.getfullargspec(self.value)
        if argspec.varkw:
            stack.insert(0, "**" + argspec.varkw)
        if argspec.varargs:
            stack.insert(0, "*" + argspec.varargs)
        defaults = list(argspec.defaults or [])
        for arg in argspec.args[::-1]:
            if defaults:
                default = defaults.pop()
                stack.insert(0, f"{arg}={default}")
            else:
                stack.insert(0, arg)
        return ", ".join(stack)

    def code(self):
        """Inspect for the code."""
        return inspect.getsource(self.value)

    def line_number(self):
        """Get the starting line number of the code inspected."""
        return inspect.getsourcelines(self.value)[1]


class Attributes(collections.abc.MutableSequence):
    """Class to ensure attributes are added following mro order."""

    def __init__(self):
        """Initiate class."""
        self.attrs = []

    def __getitem__(self, key):
        """Explicitly get based on key in attrs."""
        return self.attrs[key]

    def __setitem__(self, key, value):
        """Clean and verify before setting."""
        if key < len(self.attrs) or not isinstance(key, int):
            raise ValueError("Can't change value of position")
        if not isinstance(value, Attribute):
            raise TypeError("Can only hold Attributes")
        # find attributes higher in the mro
        existing = list(filter(lambda x: x.name == value.name, self.attrs))
        # methods can't be dirty, because they don't necessarily override
        if existing and not isinstance(value, Method):
            value.dirty = True
        elif existing:
            existing[-1].children.append(value)
            return
        self.attrs.append(value)
        self.attrs.sort(key=lambda x: x.name)

    def __delitem__(self, key):
        """Explicitly based on a key in attrs."""
        del self.attrs[key]

    def __len__(self):
        """Explicitly set length to length of attrs."""
        return len(self.attrs)

    def insert(self, index, value):
        """Overwrite the insert method."""
        self.__setitem__(index, value)  # pylint: disable=unnecessary-dunder-call


class KlassInspector:  # pylint: disable=too-many-instance-attributes
    """Inspector object to inspect a class."""

    def __init__(self, klasses, dotted_path):
        """Initialize the Class.

        Args:
            klasses (list): List of classes in dotted_path format.
            dotted_path (str): The class in questions dotted_path.
        """
        self.klasses = klasses
        self.klass_name = dotted_path.rsplit(".")[0]
        self.module_name = dotted_path.rsplit(".")[1]
        self.dotted_path = dotted_path

        self.module_path = self.klasses[self.dotted_path]["module_path"]
        self.subclass_path = self.klasses[self.dotted_path]["subclass_path"]
        self.url = self.klasses[self.dotted_path]["url"]
        self.other_klasses = {}

    def get_klass(self):
        """Load the class."""
        return import_string(self.dotted_path)

    def get_page_url(self):
        """Get the url of the class."""
        return self.klasses[self.dotted_path]["url"].split("#")[0]

    def get_klass_mro(self):
        """Get the class inheritance order or MRO."""
        ancestors = []
        for ancestor in self.get_klass().mro():
            if ancestor is object:
                break
            ancestors.append(ancestor)
            if not self.other_klasses.get(get_dotted_path(ancestor)):
                self.other_klasses[get_dotted_path(ancestor)] = get_attribute_code(
                    import_string(get_dotted_path(ancestor))
                )
        return ancestors

    def get_children(self):
        """Get children."""
        children = []
        for klass in self.klasses:
            klass = import_string(klass)
            if issubclass(klass, self.get_klass()) and klass != self.get_klass():
                children.append(klass)
        return children

    def _is_method(self, attr):
        return isinstance(attr, (types.FunctionType, types.MethodType))

    def get_attributes(self):
        """Get the attributes of the class."""
        attrs = Attributes()
        attr_dict = {}
        sorted_dict = {}

        for klass in self.get_klass_mro():
            dotted_path = get_dotted_path(klass)
            if dotted_path in self.klasses:
                attr_info = self.klasses[dotted_path]["attr_code"]
            elif dotted_path in self.other_klasses:
                attr_info = self.other_klasses[dotted_path]

            for attr_str, code in attr_info.items():
                val = Attribute(
                    name=attr_str, value=attr_str, classobject=klass, instance_class=self.get_klass(), attr_code=code
                )
                if not val.attr_code:
                    continue
                if not sorted_dict.get(attr_str):
                    sorted_dict[attr_str] = []
                sorted_dict[attr_str].append(str(klass.__name__))
                attr_dict[f"{str(klass.__name__)}___{attr_str}"] = val
        attrs = []
        # The ordering of the attributes should be printed out in alpha, then mro order.
        # MRO order is kept with the list of the lists created in `sorted_dict` and we simply
        # need to sort the keys.
        for key in sorted(sorted_dict.keys()):
            for item in sorted_dict[key]:
                attrs.append(attr_dict[f"{item}___{key}"])
        return attrs

    def get_methods(self):
        """Get the callable methods."""
        attrs = Attributes()

        for klass in self.get_klass_mro():
            for attr_str in klass.__dict__.keys():
                if attr_str.startswith("__") and not attr_str.startswith("__init__"):
                    continue
                # Occasionally you will get an attribute that is a assigned to a function
                # such as `objects = RestrictedQuerySet.as_manager()`, when this happens ensure it did
                # not fail on a method in which you would re-raise the same issue, otherwise continue on.
                try:
                    attr = getattr(klass, attr_str)
                except Exception:
                    if not is_function_attribute(klass, attr_str):
                        continue
                    raise
                if self._is_method(attr):
                    attrs.append(
                        Method(
                            name=attr_str,
                            value=attr,
                            classobject=klass,
                            instance_class=self.get_klass(),
                            attr_code=None,
                        )
                    )
        return attrs

    def get_direct_ancestors(self):
        """Filter for only the direct ancestors."""
        klass = self.get_klass()
        return klass.__bases__

    def get_unavailable_methods(self):
        """Get the unavailable methods of the class."""

        def next_token(tokensource, lookahead, is_looking_ahead):
            for ttype, value in tokensource:
                while lookahead and not is_looking_ahead:
                    yield lookahead.popleft()
                yield ttype, value

        def lookahed_token_from_iter(lookahead, next_token_iter):
            lookahead_token = next(next_token_iter)
            lookahead.append(lookahead_token)
            return lookahead_token

        not_implemented_methods = []
        for method in self.get_methods():  # pylint: disable=too-many-nested-blocks
            lookahead = collections.deque()
            lookback = collections.deque()
            is_looking_ahead = False
            tokensource = lex(inspect.getsource(method.value), PythonLexer())
            next_token_iter = next_token(tokensource, lookahead, is_looking_ahead)
            for ttype, value in next_token_iter:
                lookback.append((ttype, value))
                if ttype in Token.Name and lookback[-2][1] == "." and lookback[-3][1] == "self":
                    if not hasattr(self.get_klass(), value):
                        is_looking_ahead = True
                        try:
                            _, la_value = lookahed_token_from_iter(lookahead, next_token_iter)
                            if la_value == "(":
                                not_implemented_methods.append(value)
                        except StopIteration:
                            pass
                        is_looking_ahead = False
        return set(not_implemented_methods)


class Inspector:  # pylint: disable=too-many-instance-attributes
    """Inspector Class aggregates all of the relevant KlassInspector instances."""

    def __init__(self, strategy, base_classes_str, module_info, urls, libraries):  # pylint: disable=too-many-arguments
        """Initialize the Class.

        Args:
            strategy (list): The type of strategy used in this configuration.
            base_classes_str (str): The dotted_path of the Class in question.
            module_info (list): The list of modules to check for the base class from.
            urls (dict): The urls associated with all of the classes.
            libraries (list): A list of library paths to be interested in.
        """
        self.strategy = strategy
        self.base_classes_str = base_classes_str
        self.base_classes = [(i, import_string(i)) for i in base_classes_str]
        self.base_classes_tuple = tuple(i[1] for i in self.base_classes)
        self.modules_str = list(module_info)
        self.urls = urls
        self.libraries = libraries
        self.klasses = {}
        self.get_all_klasses()
        self.klass_details = {}
        self.klass_short = {}
        for klass in self.klasses:
            self.klass_details[klass] = KlassInspector(self.klasses, klass)
            self.klass_short[klass] = self.klass_details[klass].dotted_path

    def get_all_klasses(self):
        """Dynamically find all classes in scope."""
        for module_str in self.modules_str:
            module = importlib.import_module(module_str)
            for attr_str in dir(module):
                attr = getattr(module, attr_str)
                try:
                    issubclass(attr, (self.base_classes_tuple))
                except TypeError:
                    continue
                for base_class in self.base_classes:
                    if issubclass(attr, (base_class[1])) and not attr_str.startswith("_"):
                        if any(attr.__module__.startswith(i) for i in self.libraries):
                            url = self.get_url(module_str, base_class[0], attr.__name__)
                            self.klasses[get_dotted_path(attr)] = {
                                "module_path": module_str,
                                "subclass_path": base_class[0],
                                "url": url,
                                "attr_code": get_attribute_code(import_string(get_dotted_path(attr))),
                            }
                        break

    def get_url(self, module_str, base_class_str, name):
        """Toggle the url based on the strategy."""
        if self.strategy == "subclass":
            return self.urls[base_class_str] + f"#{name.lower()}"
        if self.strategy == "module":
            return self.urls[module_str] + f"#{name.lower()}"
        raise ValueError("Strategy not one of ('subclass', 'module').")
