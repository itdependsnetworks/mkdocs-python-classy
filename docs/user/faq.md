# Frequently Asked Questions

## How do I get a Django or other app that requires the application to be up?

MkDocs provides "hooks", you can see an example here: 

``` yaml
hooks:
    - "scripts/mkdocs-hook.py"
```

```python
# cat scripts/mkdocs-hook.py
import nautobot
from django.core.wsgi import get_wsgi_application

def on_startup(*, command, dirty):
    nautobot.setup()
    application = get_wsgi_application()

```