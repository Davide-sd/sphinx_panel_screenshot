import os

import pytest

from sphinx_panel_screenshot.utils import (
    assign_last_line_into_variable,
)

def test_assign_last_line_into_variable_1():
    # the last line of code is an expression
    code = "dashboard = IrisDashboard(name='Iris_Dashboard')\ncomponent = dashboard.panel()\ncomponent"
    new_code = assign_last_line_into_variable(code)
    assert new_code != code
    assert "mypanel" in new_code

def test_assign_last_line_into_variable_2():
    # the last line of code is an expression representing a function call
    code = "plot_something(1, 2, kw1=True, kw2=False)"
    new_code = assign_last_line_into_variable(code)
    assert new_code != code
    assert "mypanel" in new_code

def test_assign_last_line_into_variable_3():
    # the last line of code is of the type expression.servable()
    code = "plot_something(1, 2, kw1=True, kw2=False).servable()"
    new_code = assign_last_line_into_variable(code)
    assert new_code != code
    assert "mypanel" in new_code
    assert "servable" not in new_code
