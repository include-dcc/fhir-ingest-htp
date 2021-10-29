import os
from setuptools import setup, find_packages

from ncpi_fhir_utility.config import FHIR_VERSION

from ncpi_fhir_plugin import __version__

root_dir = os.path.dirname(os.path.abspath(__file__))
req_file = os.path.join(root_dir, "requirements.txt")

with open(req_file) as f:
    requirements = f.read().splitlines()

setup(
    name="include-ingest",
    version=__version__,
    description=f"INCLUDE FHIR Ingest Scripts {FHIR_VERSION}",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    scripts=["scripts/01-transform.py", "scripts/02-load.py"],
)
