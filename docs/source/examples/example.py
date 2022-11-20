def func():
    import hvplot.pandas
    import param
    import panel as pn
    from bokeh.sampledata.iris import flowers

    pn.extension(sizing_mode="stretch_width")
    inputs = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']

    class IrisDashboard(param.Parameterized):
        X_variable = param.Selector(inputs, default=inputs[0])
        Y_variable = param.Selector(inputs, default=inputs[1])

        @param.depends('X_variable', 'Y_variable')
        def plot(self):
            return flowers.hvplot.scatter(x=self.X_variable, y=self.Y_variable, by='species').opts(height=300)

        def panel(self):
            return pn.Row(
                pn.Param(self, width=200, name = "Plot Settings", sizing_mode="fixed"), 
                self.plot
            )

    dashboard = IrisDashboard(name='Iris_Dashboard')
    return dashboard.panel()