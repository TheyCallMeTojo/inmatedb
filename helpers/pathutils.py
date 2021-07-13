from pathlib import Path
import os

def get_project_dir():
    module_path = os.path.dirname(__file__)
    project_dir = Path(module_path).parent
    return str(project_dir)

def extend_relpath(relpath):
    project_dir = get_project_dir()
    return os.path.join(project_dir, relpath)
