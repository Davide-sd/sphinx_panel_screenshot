import ast

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
