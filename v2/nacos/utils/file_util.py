import os
from logging import Logger
from typing import Optional

import aiofiles

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


async def read_file(logger: Logger, file_path: str) -> str:
    """
    读取指定文件的内容。

    :param logger:  logger
    :param file_path: 文件路径
    :return: 文件内容（字符串）
    """
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            file_content = await file.read()
        return file_content
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return ""
    except PermissionError:
        logger.error(f"Permission denied to read file: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error reading file: {file_path}, error: {e}")
        return ""


async def read_all_files_in_dir(logger: Logger, dir_path: str) -> Optional[dict]:
    """
    读取指定文件夹下所有文件的内容。

    :param logger:  logger
    :param dir_path: 文件夹路径
    :return: 包含文件名和内容的字典
    """
    if not is_file_exist(dir_path):
        logger.error(f"directory not found: {dir_path}")
        return None

    if not os.path.isdir(dir_path):
        logger.error(f"path is not a directory: {dir_path}")
        return None

    try:
        file_contents = {}
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
                content = await read_file(logger, file_path)
                file_contents[file_name] = content
                continue
        return file_contents
    except Exception as e:
        logger.error(f"Error reading directory: {dir_path}, error: {e}")
        return None


async def write_to_file(logger: Logger, file_path: str, content: str) -> None:
    """
    将内容写入指定文件。

    :param logger:  logger
    :param file_path: 文件路径
    :param content: 要写入的内容
    """
    mkdir_if_necessary(os.path.dirname(file_path))

    try:
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
            await file.write(content)
    except PermissionError:
        logger.error(f"Permission denied to write file: {file_path},content: {content}")
        raise PermissionError
    except Exception as e:
        logger.error(f"Error writing to file: {file_path}, content: {content}, error: {e}")
        raise e
