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


def check_file(file_path, checksum):
    if not checksum:
        return False
    if get_file_md5(file_path) == checksum:
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


def get_checksum(package_path, checksum_dir):
    checksum_path = '%s/%s' % (checksum_dir, get_file_name_without_extension(package_path))
    if os.path.isfile(checksum_path):
        with open(checksum_path) as f:
            return f.read()
    else:
        return None


def save_checksum(checksum, package_path, checksum_dir):
    package_name = get_file_name_without_extension(package_path)
    with open('%s/%s' % (checksum_dir, package_name), 'w+') as f:
        f.truncate()
        f.write(checksum)


def remove_checksum(package_path, checksum_dir):
    checksum_path = '%s/%s' % (checksum_dir, get_file_name_without_extension(package_path))
    if os.path.isfile(checksum_path):
        os.remove(checksum_path)
