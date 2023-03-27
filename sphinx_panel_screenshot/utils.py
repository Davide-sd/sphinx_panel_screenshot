import ast
import logging
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService


def assign_last_line_into_variable(code):
    """Take the last command and assign it to a known variable name, if it's
    not already an assignment.

    If the command includes the "servable()" function call, remove it.

    Examples
    ========

    >>> code = "p = already_an_assignment(1, 2, kw1=True, kw2=False)"
    >>> assign_last_line_into_variable(code)
    p = already_an_assignment(1, 2, kw1=True, kw2=False)

    >>> code = "some_command(1, 2, kw1=True, kw2=False)"
    >>> assign_last_line_into_variable(code)
    mypanel = some_command(1, 2, kw1=True, kw2=False)

    >>> code = "some_other_command(1, 2, kw1=True, kw2=False).servable()"
    >>> assign_last_line_into_variable(code)
    mypanel = some_other_command(1, 2, kw1=True, kw2=False)

    """
    tree = ast.parse(code)
    ln = tree.body[-1]
    if isinstance(ln, ast.Assign):
        return code
    
    if isinstance(ln, ast.Expr):
        if (isinstance(ln.value, ast.Call) and
            isinstance(ln.value.func, ast.Attribute) and 
            (ln.value.func.attr == "servable")):
            # we are in this case: panel_obj.servable(). Remove servable()
            tree.body[-1] = ln.value.func.value
        
        # make an assignment
        value = tree.body[-1].value if isinstance(tree.body[-1], ast.Expr) else tree.body[-1]
        tree.body[-1] = ast.Assign(
            targets=[ast.Name(id="mypanel")], 
            value=value,
            lineno=tree.body[-1].lineno
        )
    return ast.unparse(tree)


def get_driver(browser, browser_path, driver_path, driver_options=[]):
    """Instantiate a webdriver.

    Parameters
    ----------

    browser : str
        Can be either ``"firefox"`` or ``"chrome"``.
    browser_path : str
        Location of the executable.
    driver_path : str
        Location of the driver.
    driver_options : list/tuple
        A list of strings to be added to the browser options with the
        ``add_argument`` method. Default to empty list.
    """
    if (browser is None) or (browser == "chrome"):
        logging.info("Browser: Chrome")
        options = webdriver.ChromeOptions()
        if driver_path is None:
            driver_path = ChromeDriverManager().install()
        service = ChromeService(driver_path)
        Browser = webdriver.Chrome
    else:
        logging.info("Browser: Firefox")
        options = webdriver.FirefoxOptions()
        if driver_path is None:
            driver_path = GeckoDriverManager().install()
        service = FirefoxService(driver_path)
        Browser = webdriver.Firefox

    logging.info("driver options: %s", driver_options)
    for do in driver_options:
        options.add_argument(do)

    if browser_path is not None:
        logging.info("browser_path: %s", browser_path)
        options.binary_location = browser_path
    logging.info("driver_path: %s", driver_path)

    # define a headless browser
    logging.info("Instantiating browser")
    driver = Browser(service=service, options=options)
    driver.set_window_position(0, 0)
    return driver


def set_size(t, default_size):
    """Return a tuple specifying the image size.
    """
    if not isinstance(t, (tuple, list)):
        if isinstance(t, int):
            return [t, t]
        return default_size
    if len(t) == 1:
        return [t[0], t[0]]
    return t