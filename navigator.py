import hashlib
import os
import ntpath


def get_file_unique_key(filename):
    return hashlib.md5(str(filename).encode('utf-8')).hexdigest()

class FilesTreeGenerator():
    def __init__(self, path):
        if(not os.path.isdir(path)):
            raise NotADirectoryError(path)

        dirs_dict = dict()
        root_dir = File(path, None, True)
        root_dir.name = ntpath.basename(root_dir.path)
        dirs_dict[path] = root_dir

        for root, dirs, files in os.walk(path):
            parent = dirs_dict[root]
            for dirname in dirs:
                dir = File(dirname, parent, True)
                parent.dirs.append(dir)
                dirs_dict[dir.path] = dir
            for filename in files:
                file = File(filename, parent, False)
                parent.files.append(file)
                dirs_dict[file.path] = file

        self.root_dir = root_dir
        self.dirs_dict = dirs_dict
        self.path = path


class File(object):
    def __init__(self, name, parent, is_dir):
        self.name = name
        self.parent = parent
        self.is_dir = is_dir
        self.files = []
        self.dirs = []
        self.path = name
        if(parent is not None):
            self.path = os.path.join(parent.path, name)
        self.size = 0
        if not is_dir and os.path.isfile(self.path):
            self.size = os.path.getsize(self.path)

    def __str__(self):
        return self.path


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


class Pagination():
    def __init__(self, dir, page_size):
        self.page_size = page_size
        self.current_page_num = -1

        self.dirs = dir.dirs
        self.files = dir.files
        self.all_objects = self.dirs + self.files
        self.pages = [self.all_objects[i:i+page_size] for i in range(0, len(self.all_objects), page_size)]
        self.current_page = None

        self.total_size =  len(self.all_objects)
        self.total_pages_num = len(self.pages)
        self.set_page(1)


    def set_page(self, page_number):
        if self.total_pages_num == 0:
            return False

        if page_number <= 0:
            page_number = 1

        if page_number > self.total_pages_num:
            page_number = self.total_pages_num

        if self.current_page_num == page_number:
            return False

        self.current_page_num = page_number
        self.current_page = self.pages[self.current_page_num - 1]
        return True


    def set_first_page(self):
        return self.set_page(1)

    def set_last_page(self):
        return self.set_page(self.total_pages_num)

    def set_next_page(self):
        return self.set_page(self.current_page_num + 1)

    def set_prev_page(self):
        return self.set_page(self.current_page_num - 1)

    def get_file(self, idx):
        try:
            idx = abs(int(idx))
        except ValueError:
            return None
        if(len(self.current_page) <= idx):
            return None
        return self.current_page[idx]

    def is_first_page(self):
        return self.current_page_num == 1

    def is_last_page(self):
        return self.current_page_num == (self.total_pages_num)


class Navigator():
    def __init__(self, page_size):
        self.main_root = File("/", None, True)
        self.current_dir = None
        self.pagination = None
        self.page_size = page_size
        self.set_dir(self.main_root)
        self.aliases = {}
        self.set_dir(dir=self.main_root)

    def add_files_tree(self, root, alias):
        self.aliases[root.path] = alias
        root.parent = self.main_root
        if root.is_dir:
            self.main_root.dirs.append(root)
        else:
            self.main_root.files.append(root)
        self.set_dir(dir=self.main_root)

    def find_file(self, key, is_dir):
        result = self.pagination.get_file(idx=key)
        if result is not None:
            return result
        if is_dir:
            return next((f for f in self.current_dir.dirs if f.name == key), None)
        else:
            return next((f for f in self.current_dir.files if f.name == key), None)

    def set_dir(self, dir):
        if(not isinstance(dir, File)):
            dir = self.find_file(key=dir, is_dir=True)
        if dir is None or not dir.is_dir:
            return False
        self.current_dir = dir
        self.pagination = Pagination(dir, self.page_size)
        return True

    def set_parent_dir(self):
        if self.current_dir.parent is not None:
            self.set_dir(self.current_dir.parent)

    def get_current_page_files(self):
        return self.pagination.current_page

    def next_page(self):
        return self.pagination.set_next_page()

    def prev_page(self):
        return self.pagination.set_prev_page()

    def first_page(self):
        return self.pagination.set_first_page()

    def last_page(self):
        return self.pagination.set_last_page()

    def get_file(self, key):
        return self.find_file(key=key, is_dir=False)