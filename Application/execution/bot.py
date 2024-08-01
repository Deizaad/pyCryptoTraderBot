import os
import sys
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.utils.botlogger import initialize_logger  # noqa: E402



initialize_logger()