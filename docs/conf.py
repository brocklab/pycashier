project = "Pycashier"
copyright = "2024, BrockLab"
author = "BrockLab"

extensions = ["myst_parser", "sphinx_copybutton", "sphinx_inline_tabs"]
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 1


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


html_theme = "shibuya"
# html_static_path = ["_static"]
# TODO: make a logo?
# html_logo = "../assets/logo.svg"

html_theme_options = {
    "github_url": "https://github.com/brocklab/pycashier",
    "nav_links": [
        {"title": "Documentation", "url": "installation"},
        {"title": "CLI Reference", "url": "cli"},
    ],
}
