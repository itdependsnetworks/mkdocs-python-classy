EXTRA_CSS = """<style>
.pull-right {
    float: right
}</style>"""

TEMPLATE_STRING = """
## `${name}`

``` py
${import_statment}
```

**Ancestors (MRO)**

The Method Resolution Order is described below.

${ancestors}

**Descendant Classes**

${descendants}

**Attributes**

${attributes}

**Methods**

${methods}

"""
