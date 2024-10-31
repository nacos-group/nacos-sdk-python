import os

os_type = os.name


def mkdir_if_necessary(create_dir: str):
    if os_type == 'nt' and os.path.isabs(create_dir):
        if len(create_dir) < 2 or create_dir[1] != ':':
            raise ValueError("Invalid absolute path for Windows")
    os.makedirs(create_dir, exist_ok=True)


def is_file_exist(file_path: str):
    if not file_path:
        return False
    return os.path.exists(file_path)


def read_file(file_path: str):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
        return file_content
    except IOError as e:
        raise
