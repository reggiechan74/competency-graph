"""The plugin and its dashboard page share one version number (tools/bump_version.py). Every place must state it."""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TOOL = os.path.join(ROOT, "tools", "bump_version.py")


@pytest.mark.skipif(not os.path.isfile(TOOL), reason="the skill is installed without the repository's tools folder")
def test_the_plugin_and_the_page_state_one_version_everywhere():
    sys.path.insert(0, os.path.dirname(TOOL))
    import bump_version as bv
    found = bv.versions()
    assert None not in found.values(), f"a place states no version: {found}"
    assert len(set(found.values())) == 1, f"the version differs between places (run tools/bump_version.py): {found}"
