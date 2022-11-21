# sphinx_panel_screenshot

[![PyPI version](https://badge.fury.io/py/sphinx-panel-screenshot.svg)](https://badge.fury.io/py/sphinx-panel-screenshot)
[![Conda (channel only)](https://img.shields.io/conda/vn/davide_sd/sphinx_panel_screenshot?color=%2340BA12&label=conda%20package)](https://anaconda.org/Davide_sd/sphinx_panel_screenshot)
[![Documentation Status](https://readthedocs.org/projects/sphinx-panel-screenshot/badge/?version=latest)](https://sphinx-panel-screenshot.readthedocs.io/en/latest/?badge=latest)

A Sphinx directive for including the screenshot of an holoviz's panel widget
in a Sphinx document.

_**This package is based on [matplotlib's plot directive](https://matplotlib.org/stable/api/sphinxext_plot_directive_api.html).**_

## Install

```
pip install sphinx_panel_screenshot
```

or:

```
conda install -c davide_sd sphinx_panel_screenshot 
```

Take a look at the [Installation page](https://sphinx-panel-screenshot.readthedocs.io/en/latest/install.html)
to understand how to configure the extension to run on [readthedocs.org server](https://readthedocs.org).

## Usage

```python
.. panel-screenshot::

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
```

<img src="https://raw.githubusercontent.com/Davide-sd/sphinx_panel_screenshot/master/imgs/screenshot-1.png">

Take a look at the [Examples page](https://sphinx-panel-screenshot.readthedocs.io/en/latest/examples/index.html)
to visualize the available customization options.
