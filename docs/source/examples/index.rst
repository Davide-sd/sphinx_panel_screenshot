Examples
--------

Basic example and precode
=========================

By default, the following code will be executed before running each code block.
This allows to use ``pn`` and ``np``.

.. code-block:: python

   import numpy as np
   import panel as pn
   import param

The last command of the of ``panel-screenshot`` code block must be a panel's
widget:

.. panel-screenshot::
   :context: reset
   :small-size: 400, 300

   floatslider = pn.widgets.FloatSlider(start=0, end=2, value=0.5,
      name="Float Slider")
   radiobutton_group = pn.widgets.RadioButtonGroup(
      name='Radio Button Group', options=['Biology', 'Chemistry', 'Physics'],
      button_type='success')
   radiobox_group = radio_group = pn.widgets.RadioBoxGroup(
      name='RadioBoxGroup', options=['Biology', 'Chemistry', 'Physics'], inline=True)
   select = pn.widgets.Select(name='Select',
      options=['Biology', 'Chemistry', 'Physics'])
   checkbutton_group = pn.widgets.CheckButtonGroup(name='Check Button Group',
      value=['Apple', 'Pear'],
      options=['Apple', 'Banana', 'Pear', 'Strawberry'])
   checkbox = pn.widgets.Checkbox(name='Checkbox')
   col = pn.Column(floatslider, radiobutton_group, radiobox_group, select, checkbutton_group, checkbox)
   col


context
=======

By setting ``:context: previous``, the new code block will be executed in the
context of the previous ones. To start a new context, set ``:context: reset``.

In the following example, by setting ``:context: previous`` the previous
variables can be accessed:

.. panel-screenshot::
   :context: previous
   :small-size: 400, 75

   radiobutton_group


Output Types
============

By default, the extension will create the following output types: ``html``,
``small.png``, ``large.png``, ``pdf``.

The output types can be changed with the following option on ``conf.py``:

.. code-block:: python

   # here we remove "large.png" and "pdf"
   panel_screenshot_formats = ["small.png", "html"]


Function
========

It is possible to execute a function contained on a module. The function must
return a panel's widget.

.. code-block:: python

   .. panel-screenshot:: examples/example.py func


.. panel-screenshot:: examples/example.py func
   :small-size: 700, 350


include-source
==============

By default, the extension will show the source code of the block being
executed. It is possible to deactive this behavior on a particular code block
by setting the ``include-source`` flag:

.. code-block:: python

   .. panel-screenshot::
      :include-source: False

      # your code here

To deactive this behavior globally, set the following option on ``conf.py``:

.. code-block:: python

   panel_screenshot_include_source = False




small-size and large-size
=========================

The headless browser is currently incapable of determining the dimensions of
the panel application, hence proper values should be used to generate the
screenshots. The default values are:

* ``small.png`` 512, 384
* ``large.png`` 1280, 960

To change the size on a code block basis:

.. code-block:: python

   .. panel-screenshot::
      :small-size: 700, 400
      :large-size: 1920, 1080

To set the size globally, use the following options on ``conf.py``:

.. code-block:: python

   panel_screenshot_small_size = [700, 400]
   panel_screenshot_large_size = [1920, 1080]


doctest
=======

When using the `doctest` syntax, we have to:

1. import the appropriate modules.
2. the last line must be an assignment to the ``mypanel`` variable, which is
   used by the extension to know what to render on the screenshot.

.. panel-screenshot::
   :small-size: 400, 75
   :large-size: 800, 75

   >>> import panel as pn
   >>> floatslider = pn.widgets.FloatSlider(start=0, end=2, value=0.5,
   ...     name="Float Slider")
   >>> isinstance(floatslider, pn.widgets.FloatSlider)
   True
   >>> mypanel = floatslider


intercept_code
==============

There might be occasions where the programmer needs to performs edits to the
code block being executed, without the final user to be aware of them.

To achieve that, a function accepting the current code and returning the
modified code must be assigned to ``panel_screenshot_intercept_code`` in
``conf.py``.

For example:

.. code-block:: python

   def edit_current_block(code):
      # use regex and/or ast modules, or other strategies to edit the code
      return modified_code
   
   panel_screenshot_intercept_code = edit_current_block
