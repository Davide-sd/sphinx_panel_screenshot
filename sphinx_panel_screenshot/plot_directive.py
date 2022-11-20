"""
A directive for including the screenshot of a panel app in a Sphinx document

By default, in HTML output, `panel-screenshot` will include a small.png file
with a link to a large.png, an .html and .pdf.  In LaTeX output, it will
include a .pdf.

The source code for the panel application may be included in one of three ways:

1. **A path to a source file** as the argument to the directive::

     .. panel-screenshot:: path/to/plot.py

   When a path to a source file is given, the content of the
   directive may optionally contain a caption for the plot::

     .. panel-screenshot:: path/to/plot.py

        The plot caption.

   Additionally, one may specify the name of a function to call (with
   no arguments) immediately after importing the module::

     .. panel-screenshot:: path/to/plot.py function_name

2. Using **doctest** syntax::

     .. panel-screenshot::

        A plotting example:
        >>> import matplotlib.pyplot as plt
        >>> plt.plot([1, 2, 3], [4, 5, 6])

3. Using **code block** syntax::

     .. panel-screenshot::

        floatslider = pn.widgets.FloatSlider(start=0, end=2, value=0.5, name="Float Slider")
        floatslider

Options
-------

The ``panel-screenshot`` directive supports the following options:

    format : {'python', 'doctest'}
        The format of the input.  If unset, the format is auto-detected.

    include-source : bool
        Whether to display the source code. The default can be changed using
        the `panel_screenshot_include_source` variable in :file:`conf.py` (which itself defaults to True).

    context : bool or str
        If provided, the code will be run in the context of all previous plot
        directives for which the ``:context:`` option was specified.  This only
        applies to inline code plot directives, not those run from files. If
        the ``:context: reset`` option is specified, the context is reset
        for this and future plots. ``:context: previous`` keeps the context.

    nofigs : bool
        If specified, the code block will be run, but no figures will be
        inserted.  This is usually useful with the ``:context:`` option.

    caption : str
        If specified, the option's argument will be used as a caption for the
        figure. This overwrites the caption given in the content, when the plot
        is generated from a file.
    
    small-size : width, height
        Specify the width and height (pixels) of the small-screen screenshot.

    large-size : width, height
        Specify the width and height (pixels) of the large-screen screenshot.

Additionally, this directive supports all of the options of the `image`
directive, except for *target* (since panel-screenshot will add its own
target). These include *alt*, *height*, *width*, *scale*, *align* and *class*.

Configuration options
---------------------

The panel-screenshot directive has the following configuration options:

    panel_screenshot_include_source
        Default value for the include-source option (default: True).

    panel_screenshot_html_show_source_link
        Whether to show a link to the source in HTML (default: True).

    panel_screenshot_pre_code
        Code that should be executed before each plot. If None (the default),
        it will default to a string containing::

            import numpy as np
            import param
            import panel as pn

    panel_screenshot_basedir
        Base directory, to which ``panel-screenshot::`` file names are
        relative to. If None or empty (the default), file names are relative
        to the directory where the file containing the directive is.

    panel_screenshot_formats
        File formats to generate
        (default: ``['small.png', 'large.png', 'html', 'pdf']``).
        List of tuples or strings::

            [(suffix, dpi), suffix, ...]

        that determine the file format and the DPI. For entries whose
        DPI was omitted, sensible defaults are chosen. When passing from
        the command line through sphinx_build the list should be passed as
        suffix:dpi,suffix:dpi, ...

        ``'small.png'`` refers to a small-screen browser. It is also the image
        visualized on the page.

        ``'large.png'`` refers to a large-screen browser. It is meant to
        visualize a screenshot of the application on a usual browser window.

    panel_screenshot_html_show_formats
        Whether to show links to the files in HTML (default: True).

    panel_screenshot_working_directory
        By default, the working directory will be changed to the directory of
        the example, so the code can get at its data files, if any.  Also its
        path will be added to `sys.path` so it can import any helper modules
        sitting beside it.  This configuration option can be used to specify
        a central directory (also added to `sys.path`) where data files and
        helper modules for all code are located.

    panel_screenshot_template
        Provide a customized template for preparing restructured text.
    
    panel_intercept_code : callable
        A function accepting one argument (the current code block being
        processed), returning a modified code. There might be occasions where
        the programmer needs to performs edits to the code block being
        executed, without the final user to be aware of them.
    
    panel_screenshot_small_size : (width, height)
        Specify the width and height of the small-screen screenshot.

    panel_screenshot_large_size : (width, height)
        Specify the width and height of the large-screen screenshot.

    panel_screenshot_browser : str or None
        Specify which browser to use to create screenshots. Possible options
        are ``"chrome"`` or ``"firefox"``.
        If not provided, Chrome will be used.

    panel_screenshot_browser_path : str or None
        Specify the path to the browser executable. If not provided, selenium
        will attempt to execute the browser from the system path.

    panel_screenshot_driver_path : str or None
        Specify the path to the driver executable. If not provided, selenium
        will attempt to execute the driver from the system path.
"""

import doctest
import itertools
import os
from os.path import relpath
from pathlib import Path
import re
import shutil
import sys
import textwrap
import traceback

from docutils.parsers.rst import directives, Directive
from docutils.parsers.rst.directives.images import Image
import jinja2  # Sphinx dependency.

import sphinx_panel_screenshot
from sphinx_panel_screenshot.utils import assign_last_line_into_variable

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from PIL import Image as PILImage
from io import BytesIO


# -----------------------------------------------------------------------------
# Registration hook
# -----------------------------------------------------------------------------


def _option_boolean(arg):
    if not arg or not arg.strip():
        # no argument given, assume used as a flag
        return True
    elif arg.strip().lower() in ('no', '0', 'false'):
        return False
    elif arg.strip().lower() in ('yes', '1', 'true'):
        return True
    else:
        raise ValueError(f'{arg!r} unknown boolean')


def _option_context(arg):
    if arg in [None, 'reset', 'previous']:
        return arg
    raise ValueError("Argument should be None or 'reset' or 'previous'")


def _option_format(arg):
    return directives.choice(arg, ('python', 'doctest'))


def mark_plot_labels(app, document):
    """
    To make plots referenceable, we need to move the reference from the
    "htmlonly" (or "latexonly") node to the actual figure node itself.
    """
    for name, explicit in document.nametypes.items():
        if not explicit:
            continue
        labelid = document.nameids[name]
        if labelid is None:
            continue
        node = document.ids[labelid]
        if node.tagname in ('html_only', 'latex_only'):
            for n in node:
                if n.tagname == 'figure':
                    sectname = name
                    for c in n:
                        if c.tagname == 'caption':
                            sectname = c.astext()
                            break

                    node['ids'].remove(labelid)
                    node['names'].remove(name)
                    n['ids'].append(labelid)
                    n['names'].append(name)
                    document.settings.env.labels[name] = \
                        document.settings.env.docname, labelid, sectname
                    break


class PlotDirective(Directive):
    """The ``.. plot::`` directive, as documented in the module's docstring."""

    has_content = True
    required_arguments = 0
    optional_arguments = 2
    final_argument_whitespace = False
    option_spec = {
        'alt': directives.unchanged,
        'height': directives.length_or_unitless,
        'width': directives.length_or_percentage_or_unitless,
        'scale': directives.nonnegative_int,
        'align': Image.align,
        'class': directives.class_option,
        'include-source': _option_boolean,
        'format': _option_format,
        'context': _option_context,
        'nofigs': directives.flag,
        'caption': directives.unchanged,
        'small-size': directives.positive_int_list,
        'large-size': directives.positive_int_list,
    }

    def run(self):
        """Run the plot directive."""
        try:
            return run(self.arguments, self.content, self.options,
                       self.state_machine, self.state, self.lineno)
        except Exception as e:
            raise self.error(str(e))


def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir
    app.add_directive('panel-screenshot', PlotDirective)
    app.add_config_value('panel_screenshot_pre_code', None, True)
    app.add_config_value('panel_screenshot_include_source', True, True)
    app.add_config_value('panel_screenshot_html_show_source_link', True, True)
    app.add_config_value('panel_screenshot_formats', ['small.png', 'large.png', 'html', 'pdf'], True)
    app.add_config_value('panel_screenshot_basedir', None, True)
    app.add_config_value('panel_screenshot_html_show_formats', True, True)
    app.add_config_value('panel_screenshot_working_directory', None, True)
    app.add_config_value('panel_screenshot_template', None, True)
    app.add_config_value("panel_screenshot_intercept_code", None, True)
    app.add_config_value("panel_screenshot_small_size", None, True)
    app.add_config_value("panel_screenshot_large_size", None, True)
    app.add_config_value("panel_screenshot_browser_path", None, True)
    app.add_config_value("panel_screenshot_driver_path", None, True)
    app.add_config_value("panel_screenshot_browser", None, True)
    app.connect('doctree-read', mark_plot_labels)
    metadata = {'parallel_read_safe': True, 'parallel_write_safe': True,
                'version': sphinx_panel_screenshot.__version__}
    return metadata


# -----------------------------------------------------------------------------
# Doctest handling
# -----------------------------------------------------------------------------


def contains_doctest(text):
    try:
        # check if it's valid Python as-is
        compile(text, '<string>', 'exec')
        return False
    except SyntaxError:
        pass
    r = re.compile(r'^\s*>>>', re.M)
    m = r.search(text)
    return bool(m)


# -----------------------------------------------------------------------------
# Template
# -----------------------------------------------------------------------------

TEMPLATE = """
{{ source_code }}

.. only:: html

   {% if source_link or (html_show_formats and not multi_image) %}
   (
   {%- if source_link -%}
   `Source code <{{ source_link }}>`__
   {%- endif -%}
   {%- if html_show_formats and not multi_image -%}
     {%- for img in images -%}
       {%- for fmt in img.formats -%}
         {%- if source_link or not loop.first -%}, {% endif -%}
         `{{ fmt }} <{{ dest_dir }}/{{ img.basename }}.{{ fmt }}>`__
       {%- endfor -%}
     {%- endfor -%}
   {%- endif -%}
   )
   {% endif %}

   {% for img in images %}
   .. figure:: {{ build_dir }}/{{ img.basename }}.{{ default_fmt }}
      {% for option in options -%}
      {{ option }}
      {% endfor %}

      {% if html_show_formats and multi_image -%}
        (
        {%- for fmt in img.formats -%}
        {%- if not loop.first -%}, {% endif -%}
        `{{ fmt }} <{{ dest_dir }}/{{ img.basename }}.{{ fmt }}>`__
        {%- endfor -%}
        )
      {%- endif -%}

      {{ caption }}  {# appropriate leading whitespace added beforehand #}
   {% endfor %}

.. only:: not html

   {% for img in images %}
   .. figure:: {{ build_dir }}/{{ img.basename }}.*
      {% for option in options -%}
      {{ option }}
      {% endfor -%}

      {{ caption }}  {# appropriate leading whitespace added beforehand #}
   {% endfor %}

"""

exception_template = """
.. only:: html

   [`source code <%(linkdir)s/%(basename)s.py>`__]

Exception occurred rendering plot.

"""

# the context of the plot for all directives specified with the
# :context: option
plot_context = dict()


class ImageFile:
    def __init__(self, basename, dirname):
        self.basename = basename
        self.dirname = dirname
        self.formats = []

    def filename(self, format):
        return os.path.join(self.dirname, "%s.%s" % (self.basename, format))

    def filenames(self):
        return [self.filename(fmt) for fmt in self.formats]


def out_of_date(original, derived, includes=None):
    """
    Return whether *derived* is out-of-date relative to *original* or any of
    the RST files included in it using the RST include directive (*includes*).
    *derived* and *original* are full paths, and *includes* is optionally a
    list of full paths which may have been included in the *original*.
    """
    if not os.path.exists(derived):
        return True

    if includes is None:
        includes = []
    files_to_check = [original, *includes]

    def out_of_date_one(original, derived_mtime):
        return (os.path.exists(original) and
                derived_mtime < os.stat(original).st_mtime)

    derived_mtime = os.stat(derived).st_mtime
    return any(out_of_date_one(f, derived_mtime) for f in files_to_check)


class PlotError(RuntimeError):
    pass


def _run_code(code, code_path, ns=None, function_name=None):
    """
    Import a Python module from a path, and run the function given by
    name, if function_name is not None.
    """
    intercept_code = setup.config.panel_screenshot_intercept_code
    if intercept_code is None:
        intercept_code = lambda x: x
    elif not callable(intercept_code):
        raise TypeError("`panel_screenshot_intercept_code` must be a function "
            "accepting one argument (the current code block being "
            "processed), returning a modified code.")
    code = assign_last_line_into_variable(intercept_code(code))

    # Change the working directory to the directory of the example, so
    # it can get at its data files, if any.  Add its path to sys.path
    # so it can import any helper modules sitting beside it.
    pwd = os.getcwd()
    if setup.config.panel_screenshot_working_directory is not None:
        try:
            os.chdir(setup.config.panel_screenshot_working_directory)
        except OSError as err:
            raise OSError(str(err) +
                '\n`panel_screenshot_working_directory` option in'
                'Sphinx configuration file must be a valid '
                'directory path') from err
        except TypeError as err:
            raise TypeError(str(err) +
                '\n`panel_screenshot_working_directory` option in '
                'Sphinx configuration file must be a string or '
                'None') from err
    elif code_path is not None:
        dirname = os.path.abspath(os.path.dirname(code_path))
        os.chdir(dirname)

    try:
        if ns is None:
            ns = {}
        if not ns:
            if setup.config.panel_screenshot_pre_code is None:
                exec(
                    'import numpy as np\n'
                    'import panel as pn\n'
                    'import param\n', ns)
            else:
                exec(str(setup.config.panel_screenshot_pre_code), ns)
        if "__main__" in code:
            ns['__name__'] = '__main__'

        exec(code, ns)
        if function_name is not None:
            exec("mypanel = " + function_name + "()", ns)

    except (Exception, SystemExit) as err:
        raise PlotError(traceback.format_exc()) from err
    finally:
        os.chdir(pwd)
    return ns


def get_panel_screenshot_formats(config):
    default_dpi = {'small.png': 80, 'large.png': 200, 'pdf': None, 'html': None}
    formats = []
    panel_screenshot_formats = config.panel_screenshot_formats
    for fmt in panel_screenshot_formats:
        if isinstance(fmt, str):
            if ':' in fmt:
                suffix, dpi = fmt.split(':')
                formats.append((str(suffix), int(dpi)))
            else:
                formats.append((fmt, default_dpi.get(fmt, 80)))
        elif isinstance(fmt, (tuple, list)) and len(fmt) == 2:
            formats.append((str(fmt[0]), int(fmt[1])))
        else:
            raise PlotError(
                'invalid image format "%r" in panel_screenshot_formats' % fmt)
    if any(k[0] not in default_dpi.keys() for k in formats):
        raise ValueError("Only the following formats are supported: "
            "%s\n" % list(default_dpi.keys()) +
            "\nReceived: %s" % panel_screenshot_formats)
    return formats


def _split_code_at_show(text):
    """Split code at plt.show()."""
    parts = []
    is_doctest = contains_doctest(text)
    part = []
    for line in text.split("\n"):
        if (not is_doctest and line.strip() == 'plt.show()') or \
               (is_doctest and line.strip() == '>>> plt.show()'):
            part.append(line)
            parts.append("\n".join(part))
            part = []
        else:
            part.append(line)
    if "\n".join(part).strip():
        parts.append("\n".join(part))
    return is_doctest, parts


def render_figures(code, code_path, output_dir, output_base, context,
                   function_name, config, context_reset=False,
                   close_figs=False,
                   code_includes=None, small_size=None, large_size=None):
    """
    Run a pyplot script and save the images in *output_dir*.

    Save the images under *output_dir* with file names derived from
    *output_base*
    """
    formats = get_panel_screenshot_formats(config)
    is_doctest, code_pieces = _split_code_at_show(code)
    is_doctest = contains_doctest(code)

    # Try to determine if all images already exist
    # Look for single-figure output files first
    all_exists = True
    img = ImageFile(output_base, output_dir)
    for (format, dpi) in formats:
        if context or out_of_date(code_path, img.filename(format),
                                  includes=code_includes):
            all_exists = False
            break
        img.formats.append(format)

    if all_exists:
        return [(code, [img])]

    # Then look for multi-figure output files
    results = []
    all_exists = True
    images = []
    for j in itertools.count():
        img = ImageFile('%s_%02d' % (output_base, j), output_dir)
        for fmt, dpi in formats:
            if context or out_of_date(code_path, img.filename(fmt),
                                        includes=code_includes):
                all_exists = False
                break
            img.formats.append(fmt)

        # assume that if we have one, we have them all
        if not all_exists:
            all_exists = (j > 0)
            break
        images.append(img)
    results.append((code, images))

    if all_exists:
        return results

    # We didn't find the files, so build them

    results = []
    ns = plot_context if context else {}

    if context_reset:
        plot_context.clear()

    ns = _run_code(
        doctest.script_from_examples(code) if is_doctest else code,
        code_path, ns, function_name)

    # retrieve the panel object
    panel_obj = ns["mypanel"]

    def set_size(t, default_size):
        if not isinstance(t, (tuple, list)):
            if isinstance(t, int):
                return [t, t]
            return default_size
        if len(t) == 1:
            return [t[0], t[0]]
        return t
    if small_size is None:
        small_size = set_size(setup.config.panel_screenshot_small_size, [512, 384])
    if large_size is None:
        large_size = set_size(setup.config.panel_screenshot_large_size, [1280, 960])

    img = ImageFile(output_base, output_dir)
    
    try:
        # TODO: can it be done better?
        fmts = [t[0] for t in formats]
        formats = {t[0]: t[1] for t in formats}

        # first, save html
        panel_obj.save(img.filename("html"))

        # generate pictures
        if ((setup.config.panel_screenshot_browser is None) or
            (setup.config.panel_screenshot_browser == "chrome")):
            options = webdriver.ChromeOptions()
            options.headless = True
            options.add_argument("--disable-dev-shm-usage"); # overcome limited resource problems
            options.add_argument("--no-sandbox") # Bypass OS security model
            if setup.config.panel_screenshot_driver_path is not None:
                driver_path = setup.config.panel_screenshot_driver_path
            else:
                driver_path = ChromeDriverManager().install()
            service = ChromeService(driver_path)
            Browser = webdriver.Chrome
        else:
            options = webdriver.FirefoxOptions()
            # options.headless = True   # doesn't work...
            options.add_argument("--headless")
            if setup.config.panel_screenshot_driver_path is not None:
                driver_path = setup.config.panel_screenshot_driver_path
            else:
                driver_path = GeckoDriverManager().install()
            service = FirefoxService(driver_path)
            Browser = webdriver.Firefox

        
        if setup.config.panel_screenshot_browser_path is not None:
            options.binary_location = setup.config.panel_screenshot_browser_path

        # define a headless browser
        driver = Browser(service=service, options=options)
        driver.set_window_position(0, 0)
        # load html file into the browser
        driver.get('file://' + img.filename("html"))
        
        pil_image = None
        spng, lpng, pdf, html = "small.png", "large.png", "pdf", "html"
        
        if (spng in fmts) or (pdf in fmts):
            driver.set_window_size(*small_size)
            png = driver.get_screenshot_as_png()
            pil_image = PILImage.open(BytesIO(png))
            if spng in fmts:
                dpi = formats[spng]
                pil_image.save(img.filename(spng), dpi=(dpi, dpi))
                img.formats.append(spng)

        if (lpng in fmts) or (pdf in fmts):
            driver.set_window_size(*large_size)
            png = driver.get_screenshot_as_png()
            pil_image = PILImage.open(BytesIO(png))
            if lpng in fmts:
                dpi = formats[lpng]
                pil_image.save(img.filename(lpng), dpi=(dpi, dpi))
                img.formats.append(lpng)
        
        if html in fmts:
            img.formats.append(html)

        if pdf in fmts:
            pil_image.convert('RGB').save(img.filename(pdf))
            img.formats.append(pdf)
        
        driver.quit()
    except Exception as err:
        raise PlotError(traceback.format_exc()) from err

    results.append((code, [img]))

    return results


def run(arguments, content, options, state_machine, state, lineno):
    document = state_machine.document
    config = document.settings.env.config
    nofigs = 'nofigs' in options
    formats = get_panel_screenshot_formats(config)
    default_fmt = formats[0][0]

    options.setdefault('include-source', config.panel_screenshot_include_source)
    if 'class' in options:
        # classes are parsed into a list of string, and output by simply
        # printing the list, abusing the fact that RST guarantees to strip
        # non-conforming characters
        options['class'] = ['plot-directive'] + options['class']
    else:
        options.setdefault('class', ['plot-directive'])
    keep_context = 'context' in options
    context_opt = None if not keep_context else options['context']

    rst_file = document.attributes['source']
    rst_dir = os.path.dirname(rst_file)

    if len(arguments):
        if not config.panel_screenshot_basedir:
            source_file_name = os.path.join(setup.app.builder.srcdir,
                                            directives.uri(arguments[0]))
        else:
            source_file_name = os.path.join(setup.confdir, config.panel_screenshot_basedir,
                                            directives.uri(arguments[0]))

        # If there is content, it will be passed as a caption.
        caption = '\n'.join(content)

        # Enforce unambiguous use of captions.
        if "caption" in options:
            if caption:
                raise ValueError(
                    'Caption specified in both content and options.'
                    ' Please remove ambiguity.'
                )
            # Use caption option
            caption = options["caption"]

        # If the optional function name is provided, use it
        if len(arguments) == 2:
            function_name = arguments[1]
        else:
            function_name = None

        code = Path(source_file_name).read_text(encoding='utf-8')
        output_base = os.path.basename(source_file_name)
    else:
        source_file_name = rst_file
        code = textwrap.dedent("\n".join(map(str, content)))
        counter = document.attributes.get('_plot_counter', 0) + 1
        document.attributes['_plot_counter'] = counter
        base, ext = os.path.splitext(os.path.basename(source_file_name))
        output_base = '%s-%d.py' % (base, counter)
        function_name = None
        caption = options.get('caption', '')

    base, source_ext = os.path.splitext(output_base)
    if source_ext in ('.py', '.rst', '.txt'):
        output_base = base
    else:
        source_ext = ''

    # ensure that LaTeX includegraphics doesn't choke in foo.bar.pdf filenames
    output_base = output_base.replace('.', '-')

    # is it in doctest format?
    is_doctest = contains_doctest(code)
    if 'format' in options:
        if options['format'] == 'python':
            is_doctest = False
        else:
            is_doctest = True

    # determine output directory name fragment
    source_rel_name = relpath(source_file_name, setup.confdir)
    source_rel_dir = os.path.dirname(source_rel_name).lstrip(os.path.sep)

    # build_dir: where to place output files (temporarily)
    build_dir = os.path.join(os.path.dirname(setup.app.doctreedir),
                             'panel_screenshot_directive',
                             source_rel_dir)
    # get rid of .. in paths, also changes pathsep
    # see note in Python docs for warning about symbolic links on Windows.
    # need to compare source and dest paths at end
    build_dir = os.path.normpath(build_dir)
    os.makedirs(build_dir, exist_ok=True)

    # output_dir: final location in the builder's directory
    dest_dir = os.path.abspath(os.path.join(setup.app.builder.outdir,
                                            source_rel_dir))
    os.makedirs(dest_dir, exist_ok=True)

    # how to link to files from the RST file
    dest_dir_link = os.path.join(relpath(setup.confdir, rst_dir),
                                 source_rel_dir).replace(os.path.sep, '/')
    try:
        build_dir_link = relpath(build_dir, rst_dir).replace(os.path.sep, '/')
    except ValueError:
        # on Windows, relpath raises ValueError when path and start are on
        # different mounts/drives
        build_dir_link = build_dir
    source_link = dest_dir_link + '/' + output_base + source_ext

    # get list of included rst files so that the output is updated when any
    # plots in the included files change. These attributes are modified by the
    # include directive (see the docutils.parsers.rst.directives.misc module).
    try:
        source_file_includes = [os.path.join(os.getcwd(), t[0])
                                for t in state.document.include_log]
    except AttributeError:
        # the document.include_log attribute only exists in docutils >=0.17,
        # before that we need to inspect the state machine
        possible_sources = {os.path.join(setup.confdir, t[0])
                            for t in state_machine.input_lines.items}
        source_file_includes = [f for f in possible_sources
                                if os.path.isfile(f)]
    # remove the source file itself from the includes
    try:
        source_file_includes.remove(source_file_name)
    except ValueError:
        pass

    # make figures
    try:
        results = render_figures(
            code,
            source_file_name,
            build_dir,
            output_base,
            keep_context,
            function_name,
            config,
            context_reset=context_opt == 'reset',
            code_includes=source_file_includes,
            small_size=options["small-size"] if "small-size" in options.keys() else None,
            large_size=options["large-size"] if "large-size" in options.keys() else None
        )
        errors = []
    except PlotError as err:
        reporter = state.memo.reporter
        sm = reporter.system_message(
            2, "Exception occurred in plotting {}\n from {}:\n{}".format(
                output_base, source_file_name, err),
            line=lineno)
        results = [(code, [])]
        errors = [sm]

    # Properly indent the caption
    caption = '\n' + '\n'.join('      ' + line.strip()
                               for line in caption.split('\n'))
    
    # generate output restructuredtext
    total_lines = []
    for j, (code_piece, images) in enumerate(results):
        if options['include-source']:
            if is_doctest:
                lines = ['', *code_piece.splitlines()]
            else:
                lines = ['.. code-block:: python', '',
                         *textwrap.indent(code_piece, '    ').splitlines()]
            source_code = "\n".join(lines)
        else:
            source_code = ""

        if nofigs:
            images = []

        opts = [
            ':%s: %s' % (key, val) for key, val in options.items()
            if key in ('alt', 'height', 'width', 'scale', 'align', 'class')]

        # Not-None src_link signals the need for a source link in the generated
        # html
        if j == 0 and config.panel_screenshot_html_show_source_link:
            src_link = source_link
        else:
            src_link = None

        result = jinja2.Template(config.panel_screenshot_template or TEMPLATE).render(
            default_fmt=default_fmt,
            dest_dir=dest_dir_link,
            build_dir=build_dir_link,
            source_link=src_link,
            multi_image=len(images) > 1,
            options=opts,
            images=images,
            source_code=source_code,
            html_show_formats=config.panel_screenshot_html_show_formats and len(images),
            caption=caption)

        total_lines.extend(result.split("\n"))
        total_lines.extend("\n")

    if total_lines:
        state_machine.insert_input(total_lines, source=source_file_name)

    # copy image files to builder's output directory, if necessary
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    for code_piece, images in results:
        for img in images:
            for fn in img.filenames():
                destimg = os.path.join(dest_dir, os.path.basename(fn))
                if fn != destimg:
                    shutil.copyfile(fn, destimg)

    # copy script (if necessary)
    if config.panel_screenshot_html_show_source_link:
        Path(dest_dir, output_base + source_ext).write_text(
            doctest.script_from_examples(code)
            if source_file_name == rst_file and is_doctest
            else code,
            encoding='utf-8')

    return errors
