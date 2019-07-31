import hashlib
import os
import zipfile


def get_file_name(path):
    if path:
        return path.replace("\\", "/").split("/")[-1]
    else:
        return None


def get_file_name_without_extension(path):
    if path:
        return path.replace("\\", "/").split("/")[-1].split(".")[0]
    else:
        return None


def get_version(file_name):
    if file_name:
        return file_name.split("_")[-1].split(".")[0]
    else:
        return '0'


def get_version_from_path(path):
    return get_version(get_file_name(path))


def unzip(src_file, dest_dir):
    zf = zipfile.ZipFile(src_file)
    try:
        zf.extractall(path=dest_dir)
        return True
    except RuntimeError as e:
        print(e.args)
        return False


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
