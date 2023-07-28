# mkdocs-python-classy

<p align="center">

  <img src="https://raw.githubusercontent.com/itdependsnetworks/mkdocs-python-classy/develop/docs/images/icon-mkdocs-python-classy.png" class="logo" height="100px">
  <br>
  <!-- <a href="https://github.com/networktocode/mkdocs-python-classy/actions"><img src="https://github.com/networktocode/mkdocs-python-classy/actions/workflows/ci.yml/badge.svg?branch=main"></a> -->
  <a href="/en/latest"><img src="https://readthedocs.org/projects/mkdocs-python-classy/badge/"></a>
  <a href="https://pypi.org/project/mkdocs-python-classy/"><img src="https://img.shields.io/pypi/v/mkdocs-python-classy"></a>
  <a href="https://pypi.org/project/mkdocs-python-classy/"><img src="https://img.shields.io/pypi/dm/mkdocs-python-classy"></a>
  <br>
  <!-- TODO: Replace: /en/latest with https://mkdocs-python-classy.readthedocs.io/en/latest -->
</p>

## Overview

A MkDocs plugin that helps you navigate the infuriating challenge of understanding a nested a Python class object. Trying to determine what attributes are available or what method does the class provide, and ultimately understanding the entire MRO (Method Resolution Order).

## Screenshots

The library works like any other mkdocs plugin.

From here you can see how the MRO is described, links to other Classes covered in the docs, and a convenience Python import config.

![MRO](https://raw.githubusercontent.com/itdependsnetworks/mkdocs-python-classy/develop/docs/images/ui-view1.png)

From here you can see the details of the attributes on the class.

![Attributes](https://raw.githubusercontent.com/itdependsnetworks/mkdocs-python-classy/develop/docs/images/ui-view2.png)

From here you can see how the code of the method is shown with line numbers, it is collapsible, and will even show multiple if the method is provided in multiple Classes in the MRO order! Additionally you can see the naviagation pane that is auto generated.

![Methods](https://raw.githubusercontent.com/itdependsnetworks/mkdocs-python-classy/develop/docs/images/ui-view3.png)

## Documentation

Full web-based HTML documentation for this library can be found over on the [mkdocs-python-classy Docs](https://mkdocs-python-classy.readthedocs.io) website:

- [User Guide](/en/latest/user/lib_overview/) - Overview, Using the library, Getting Started.
- [Administrator Guide](/en/latest/admin/install/) - How to Install, Configure, Upgrade, or Uninstall the library.
- [Developer Guide](/en/latest/dev/contributing/) - Extending the library, Code Reference, Contribution Guide.
- [Release Notes / Changelog](/en/latest/admin/release_notes/).
- [Frequently Asked Questions](/en/latest/user/faq/).

### Contributing to the Docs

All the Markdown source for the library documentation can be found under the [docs](https://github.com/itdependsnetworks/mkdocs-python-classy/tree/develop/docs) folder in this repository. For simple edits, a Markdown capable editor is sufficient - clone the repository and edit away.

If you need to view the fully generated documentation site, you can build it with [mkdocs](https://www.mkdocs.org/). A container hosting the docs will be started using the invoke commands (details in the [Development Environment Guide](/en/latest/dev/dev_environment/#docker-development-environment)) on [http://localhost:8001](http://localhost:8001). As your changes are saved, the live docs will be automatically reloaded.

Any PRs with fixes or improvements are very welcome!

### Attribution

This project is largely based on the work of [Classy Class-Based Views.](https://ccbv.co.uk/) and [Classy Django REST Framework](https://www.cdrf.co/), see - [Attribution](/en/latest/dev/contributing/) for more details.

## Questions

<!-- For any questions or comments, please check the [FAQ](/en/latest/user/faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#networktocode`), sign up [here](http://slack.networktocode.com/) if you don't have an account. -->
