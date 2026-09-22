"""Make the src-layout package importable during a source checkout test run.

The installed package remains the supported runtime path.  Adding ``src``
here also makes a freshly downloaded repository testable from PyCharm or a
terminal before an editable install has been performed.
"""

from pathlib import Path
import sys


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
