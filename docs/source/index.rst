Welcome to sphinx-panel-screenshot documentation!
===================================================

``sphinx-panel-screenshot`` is a Sphinx extension to capture an image
of an `holoviz's panel <https://panel.holoviz.org/index.html>`_
application and include it into a Sphinx documentation page.

This extension aims to solve the following problem: including the html
(and JS+CSS) of a web application into a Sphinx documentation page could slow
down the loading of the page. Further, if multiple web applications were to
be included, an unnecessarily huge bandwith might be used. In this situations,
a better approach is to include a small resolution screenshot of the
application, which conveys almost the same information to the final user.
The extension also exposes an URL to the HTML file containing the application,
in case someone is interested in a closer look.

Currently, the following output types are supported:

* `html`: creates an HTML file of the application.
* `small.png`: loads the html file to an headless browser and creates a
  screenshot based on a customizable small-screen device. This is the picture
  that will be shown on the documentation page.
* `large.png`: loads the html file to an headless browser and creates a
  screenshot based on a customizable large-screen device.
* `pdf`: creates a PDF starting from one of the screenshots.


Note that this extension is based on `Matplotlib's plot directive <https://matplotlib.org/stable/api/sphinxext_plot_directive_api.html>`_.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install.rst
   panel_screenshot.rst
   examples/index.rst
   changelog.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
