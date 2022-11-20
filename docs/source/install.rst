Installation
------------



This extension can be installed with:

```
pip install sphinx_panel_screenshot
```

It will install the following requirements: panel, selenium, webdriver_manager,
sphinx, pillow.

The screenshots will be created with some headless web browser.
However, no browser and no driver will be installed by this extension.
That's left to the user.


Configuring the extension
=========================

The configuration depends on the machine in which the extension will be
executed.

If the extension is going to be executed on a `readthedocs.org <https://readthedocs.org/>`_ server, then the intended browser (Firefox or Chrome) and
the respective driver (`geckodriver <https://github.com/mozilla/geckodriver>`_ or `webdriver <https://chromedriver.chromium.org/downloads>`_ ) must be downloaded. This can be achieved by customizing the build. For example,
the ``.readthedocs.yml`` used by this extension is:

.. literalinclude:: ../../.readthedocs.yml
   :language: yaml

Then, on the documentation's ``conf.py`` we can set the following
variables:

.. code-block:: python

    import os

    # Select the browser. If omitted, Chrome will be used.
    panel_screenshot_browser = "chrome" # "chrome" or "firefox"

    # Paths to the executables. If omitted, selenium will attempt to run
    # the executables from the system $PATH.
    # The paths must match the ones created on .readthedocs.yml
    home_folder = os.path.expanduser("~")
    panel_screenshot_browser_path = os.path.join(home_folder, "selenium/chrome-linux/chrome")
    panel_screenshot_driver_path = os.path.join(home_folder, "selenium/drivers/chromedriver")
