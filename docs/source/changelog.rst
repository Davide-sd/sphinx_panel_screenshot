Changelog
---------

0.2.0
=====

* Added ``panel_screenshot_driver_options`` configuration option, which can be
  used to set an headless driver, or to request the driver to use particular
  settings.

* **Breaking:** starting from this version, by default the browser is not run
  in headless mode. User need to set 
  ``panel_screenshot_driver_options=["--headless"]`` in the configuration file.

* Added ``panel_screenshot_modify_driver`` configuration option.

* Better code organization.


0.1.3
=====

* Added ability to specify PDF resolution.
* If ``"html"`` is not specified in the output formats, the html file will be
  removed from the build, making the resulting documentation more space
  efficient.

0.1.2
=====

* Updated documentation.
* Code cleanup.


0.1.1
=====

Updated documentation.


0.1.0
=====

Initial release.