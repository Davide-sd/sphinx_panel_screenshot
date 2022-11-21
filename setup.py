from setuptools import setup, find_packages
import os

def readme():
    with open("README.md") as f:
        return f.read()

here = os.path.dirname(os.path.abspath(__file__))
version_ns = {}
with open(os.path.join(here, 'sphinx_panel_screenshot', '_version.py')) as f:
    exec (f.read(), {}, version_ns)

setup(
    name="sphinx_panel_screenshot",
    version=version_ns["__version__"],
    description="A directive to include panel's screenshots into a Sphinx document",
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Topic :: Documentation",
        "Topic :: Documentation :: Sphinx",
    ],
    keywords="panel sphinx screenshot",
    url="https://github.com/Davide-sd/sphinx_panel_screenshot",
    author="Davide Sandona",
    author_email="sandona.davide@gmail.com",
    license="MIT License",
    packages=find_packages(exclude=("tests", )),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "panel",
        "selenium",
        "webdriver_manager",
        "sphinx",
        "pillow",
    ],
    extras_require={
        "dev": [
            "pytest",
            "hvplot",
        ]
    }
)
