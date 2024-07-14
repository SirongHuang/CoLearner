import os 
import hashlib
import time
from functools import wraps

def runtime(func):
    """Print the runtime of the decorated function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        run_time = end_time - start_time
        print(f"{func.__name__} took {run_time:.4f} seconds to execute.")
        return result
    return wrapper

def create_folder(folder_path:str):
    """Create a folder in the given path if it does not exist."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        
def save_file(file, file_path: str):
    """Save a file to the given path, given the file content if it does not exist."""
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(file.getvalue())

def get_file_hash(file):
    """Read the file content and create a hash.""" 
    content = file.read()
    file.seek(0)  # Reset file pointer to beginning
    return hashlib.md5(content).hexdigest()

