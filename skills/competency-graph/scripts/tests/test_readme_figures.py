"""The README's drawings are exported from the dashboard page (tools/export_figures.py). They must match the page."""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TOOL = os.path.join(ROOT, "tools", "export_figures.py")


@pytest.mark.skipif(not os.path.isfile(TOOL), reason="the skill is installed without the repository's tools folder")
def test_the_readmes_drawings_are_the_pages_own():
    sys.path.insert(0, os.path.dirname(TOOL))
    import export_figures as ef
    files = ef.build()
    assert len(files) == 2 * len(ef.NAMES)                       # each drawing, light and dark
    for name, text in files.items():
        path = os.path.join(ef.OUT, name)
        assert os.path.isfile(path), f"docs/images/{name} is missing: run tools/export_figures.py"
        assert open(path, encoding="utf-8").read() == text, f"docs/images/{name} is out of date: run tools/export_figures.py"
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    for stem in ef.NAMES.values():                               # and the README shows every one, both ways
        assert f"docs/images/{stem}.svg" in readme and f"docs/images/{stem}-dark.svg" in readme
