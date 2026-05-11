# -- Project information -----------------------------------------------------

project = 'Student Finance Tracker'
copyright = '2026, Group 2E'
author = 'Group 2E'
release = '1.0'
version = '1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',        # Auto-generate docs from docstrings
    'sphinx.ext.viewcode',       # Add links to source code
    'sphinx.ext.napoleon',       # Support Google/NumPy style docstrings
    'sphinx.ext.todo',           # Support .. todo:: directives
    'sphinx.ext.intersphinx',    # Link to other Sphinx docs
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Show todo items in output
todo_include_todos = True

# Intersphinx: link to Python docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for HTML output -------------------------------------------------

# pip install furo
html_theme = 'furo'

html_title = 'Student Finance Tracker'

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
    "light_css_variables": {
        "color-brand-primary": "#2563eb",
        "color-brand-content": "#1d4ed8",
        "color-admonition-background": "#eff6ff",
    },
    "dark_css_variables": {
        "color-brand-primary": "#60a5fa",
        "color-brand-content": "#93c5fd",
    },
}

html_static_path = ['_static']

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
