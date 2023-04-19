import types
import collections
import inspect
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token
from mkdocs_python_classy.utils import import_string, dotted_path
import importlib


class Attribute(object):
    def __init__(self, name, value, classobject, instance_class):
        self.name = name
        self.value = value
        self.classobject = classobject
        self.instance_class = instance_class
        self.dirty = False

    @property
    def repr_value(self):
        return repr(self.value)

    def __eq__(self, obj):
        return self.name == obj.name and self.value == obj.value

    def __neq__(self, obj):
        return not self.__eq__(obj)


class Method(Attribute):
    def __init__(self, *args, **kwargs):
        super(Method, self).__init__(*args, **kwargs)
        self.children = []

    def params_string(self):
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
                stack.insert(0, "{}={}".format(arg, default))
            else:
                stack.insert(0, arg)
        return ", ".join(stack)

    def code(self):
        return inspect.getsource(self.value)

    def line_number(self):
        return inspect.getsourcelines(self.value)[1]


class Attributes(collections.abc.MutableSequence):
    # Attributes must be added following mro order
    def __init__(self):
        self.attrs = []

    def __getitem__(self, key):
        return self.attrs[key]

    def __setitem__(self, key, value):
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
        del self.attrs[key]

    def __len__(self):
        return len(self.attrs)

    def insert(self, i, x):
        self.__setitem__(i, x)


class Inspector(object):
    def __init__(self, klasses, dotted):
        self.klasses = klasses
        self.klass_name = dotted.rsplit(".")[0]
        self.module_name = dotted.rsplit(".")[1]
        self.dotted = dotted

        self.module_path = self.klasses[self.dotted]["module_path"]
        self.subclass_path = self.klasses[self.dotted]["subclass_path"]
        self.url = self.klasses[self.dotted]["url"]

    def get_klass(self):
        return import_string(self.dotted)

    def get_page_url(self):
        return self.klasses[self.dotted]["url"].split("#")[0]

    def get_klass_mro(self):
        ancestors = []
        for ancestor in self.get_klass().mro():
            if ancestor is object:
                break
            ancestors.append(ancestor)
        return ancestors

    def get_children(self):
        children = []
        for klass in self.klasses:
            klass = import_string(klass)
            if issubclass(klass, self.get_klass()) and klass != self.get_klass():
                children.append(klass)
        return children

    def _is_method(self, attr):
        return isinstance(attr, (types.FunctionType, types.MethodType))

    def get_attributes(self):
        attrs = Attributes()

        for klass in self.get_klass_mro():
            for attr_str in klass.__dict__.keys():
                attr = getattr(klass, attr_str)
                if not attr_str.startswith("__") and not self._is_method(attr):
                    attrs.append(
                        Attribute(
                            name=attr_str,
                            value=attr,
                            classobject=klass,
                            instance_class=self.get_klass(),
                        )
                    )
        return attrs

    def get_methods(self):
        attrs = Attributes()

        for klass in self.get_klass_mro():
            for attr_str in klass.__dict__.keys():
                attr = getattr(klass, attr_str)
                if not attr_str.startswith("__") and self._is_method(attr):
                    attrs.append(
                        Method(
                            name=attr_str,
                            value=attr,
                            classobject=klass,
                            instance_class=self.get_klass(),
                        )
                    )
        return attrs

    def get_direct_ancestors(self):
        klass = self.get_klass()
        return klass.__bases__

    def get_unavailable_methods(self):
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
        for method in self.get_methods():
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


class InspectorGeneral(object):
    def __init__(self, strategy, base_classes_str, module_info, urls, libraries):
        self.strategy = strategy
        self.base_classes_str = base_classes_str
        self.base_classes = [(i, import_string(i)) for i in base_classes_str]
        self.base_classes_tuple = tuple([i[1] for i in self.base_classes])
        self.modules_str = list(module_info)
        self.urls = urls
        self.libraries = libraries
        self.klasses = {}
        self.get_all_klasses()
        self.klass_details = {}
        self.klass_short = {}
        for klass in self.klasses:
            self.klass_details[klass] = Inspector(self.klasses, klass)
            self.klass_short[klass] = self.klass_details[klass].dotted

    def get_all_klasses(self):
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
                        if any([attr.__module__.startswith(i) for i in self.libraries]):
                            url = self.get_url(module_str, base_class[0], attr.__name__)
                            self.klasses[dotted_path(attr)] = {
                                "module_path": module_str,
                                "subclass_path": base_class[0],
                                "url": url,
                            }
                        break

    def get_url(self, module_str, base_class_str, name):
        if self.strategy == "subclass":
            return self.urls[base_class_str] + f"#{name.lower()}"
        elif self.strategy == "module":
            return self.urls[module_str] + f"#{name.lower()}"
        raise ValueError("Strategy not one of ('subclass', 'module').")
