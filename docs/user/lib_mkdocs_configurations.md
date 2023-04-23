# MkDocs Configurations

To determine the Classes that are in scope, the following are considered:

- What modules (or files) to consider?
- What subclass are you looking for?
- What library should be considered?

These configurations are all in dotted_path format, so given an import statement of `from django.core.exceptions import ValidationError` the dotted string would be `django.core.exceptions.ValidationError`. This concept is used extensively in Django and would refer to their [documentation](https://docs.djangoproject.com/en/4.2/ref/utils/#django.utils.module_loading.import_string).

The configurations that the plugin is looking for:

| Parameter | Description | Type | Default |
| --------- | ----------- | ---- | ------- |
| classy_strategy | Whether or not the page should be based on the module/file where code is found, or the subclass in the MRO. | Choice(subclass, module ) | subclass|
| classy_modules | A list of modules to check against. |  | list(str) in dotted path format | N/A |
| classy_subclasses | A list of modules to check against. | list(str) in dotted path format | N/A |
| classy_libraries | A list of library paths that start with to check against. | list(str) in dotted path format | N/A |


## Subclass Strategy

The below example shows what the configuration looks like if you are using the `subclass` strategy, in which each page is based on a subclass. 

``` yaml
# cat mkdocs.yml
plugins:
  - "mkdocs-python-classy":
      classy_strategy: "subclass"
      classy_modules:
      - "nautobot.apps.filters"
      - "nautobot.apps.forms"
      - "nautobot.apps.models"
      - "nautobot.apps.tables"
      - "nautobot.apps.testing"
      - "nautobot.apps.ui"
      - "nautobot.apps.urls"
      - "nautobot.apps.views"
      - "nautobot.extras.forms.base"
      classy_libraries:
      - "nautobot"

nav:
  - Overview: "index.md"
  - Classy Code Reference:
      - Views: "classy/views.md"
      - Forms: "classy/forms.md"
```

An example markdown page would look like:

```
---
classy_dotted_path: django_filters.FilterSet
---

## Classy Doc
```

> Note: The document must be a valid mkdocs markdown document. This means the yaml must follow the [YAML Style Meta-Data](https://www.mkdocs.org/user-guide/writing-your-docs/#yaml-style-meta-data) and there must be a valid markdown document below that. This markdown will be overwritten, so you can safely always use the `## Classy Doc` as an example.

## Module Strategy

Now the same for the `module` strategy:

``` yaml
plugins:
  - "mkdocs-python-classy":
      classy_strategy: "module"
      classy_subclasses:
      - "django.views.View"
      - "django.forms.Form"
      - "django_tables2.Table"
      - "django_filters.FilterSet"
      - "nautobot.core.api.serializers.BaseModelSerializer"
      classy_libraries:
      - "nautobot"

nav:
  - Overview: "index.md"
  - Classy Code Reference:
      - Views: "classy/filters.md"
      - Forms: "classy/forms.md"
```

An example markdown page would look like:


```
---
classy_dotted_path: nautobot.apps.filters
---

## Classy Doc
```

> Note: The document must be a valid mkdocs markdown document. This means the yaml must follow the [YAML Style Meta-Data](https://www.mkdocs.org/user-guide/writing-your-docs/#yaml-style-meta-data) and there must be a valid markdown document below that. This markdown will be overwritten, so you can safely always use the `## Classy Doc` as an example.