
import sys
import os
# load all of the common fixtures used by the mocked tests
pytest_plugins = ["mock.fixtures.mocked_services"]
# Added for import of services modules in tests
sys.path.insert(0, os.path.abspath("services"))