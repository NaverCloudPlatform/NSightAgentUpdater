import hashlib
import os


def get_file_name(path):
    if not path:
        return None
    return path.replace("\\", "/").split("/")[-1]


def get_file_name_without_extension(path):
    if not path:
        return None
    return path.replace("\\", "/").split("/")[-1].split(".")[0]


def get_version(file_name):
    if not file_name:
        return '0'
    return file_name.split("_")[-1].split(".")[0]


def get_version_from_path(path):
    return get_version(get_file_name(path))


def check_file(file_path, check_code=None):
    if not check_code:
        return True
    if get_file_md5(file_path) == check_code:
        return True
    else:
        return False


def get_file_md5(filename):
    if not os.path.isfile(filename):
        return
    myhash = hashlib.md5()
    with open(filename, 'rb') as f:
        while True:
            b = f.read(8096)
            if not b:
                break
            myhash.update(b)
        f.close()
        return myhash.hexdigest()
