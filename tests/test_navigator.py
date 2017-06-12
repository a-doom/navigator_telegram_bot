import unittest
import navigator as n
import math
from unittest.mock import MagicMock

def create_get_files_tree_func(root_path, dirs_num = 5, files_num = 5, depth = 2):
    def create_files_tree(dirs_num = 5, file_num = 5, depth = 2, root_dir = None, dirs_dict = None):
        dirs_dict = dirs_dict or dict()
        for i in range(dirs_num):
            filename = "dir_{0}".format(i)
            dir = n.File(filename, root_dir, True)
            if(depth > 1):
                create_files_tree(dirs_num, file_num, (depth - 1), dir)
            root_dir.dirs.append(dir)
            dirs_dict[dir.path] = dir
        for i in range(file_num):
            filename = "file_{0}".format(i)
            file = n.File(filename, root_dir, False)
            root_dir.files.append(file)
            dirs_dict[file.path] = file
        return root_dir

    root_dir = n.File(root_path, None, True)
    dirs = dict()
    dirs[root_dir.path] = root_dir
    create_files_tree(
        dirs_num,
        files_num,
        depth,
        root_dir=root_dir,
        dirs_dict=dirs)
    return root_dir, dirs



class TestNavigator(unittest.TestCase):
    def test_init_1(self):
        page_size = 7
        paths = ["path_1", "path_2"]

        navigator = n.Navigator(page_size=page_size)
        for path in paths:
            root, _ = create_get_files_tree_func(root_path=path)
            navigator.add_files_tree(root, path)

        self.assertEqual(len(navigator.main_root.dirs), len(paths))


    def test_set_dir(self):
        page_size = 7
        path_1 = "path_1"
        path_2 = "path_2"
        paths = [path_1, path_2]

        navigator = n.Navigator(page_size=page_size)
        for path in paths:
            root, _ = create_get_files_tree_func(root_path=path)
            navigator.add_files_tree(root, path)

        navigator.set_dir(path_1)
        self.assertEqual(navigator.current_dir.name, path_1)
        navigator.set_dir("invalid path")
        self.assertEqual(navigator.current_dir.name, path_1)

    def test_set_parent_dir_1(self):
        page_size = 7
        path_1 = "path_1"
        path_2 = "path_2"
        paths = [path_1, path_2]

        navigator = n.Navigator(page_size=page_size)
        for path in paths:
            root, _ = create_get_files_tree_func(root_path=path)
            navigator.add_files_tree(root, path)

        navigator.set_dir(path_1)
        self.assertEqual(navigator.current_dir.name, path_1)

        navigator.set_parent_dir()
        navigator.set_dir(path_2)
        self.assertEqual(navigator.current_dir.name, path_2)

    def test_set_parent_dir_2(self):
        page_size = 7
        path_1 = "path_1"
        path_2 = "path_2"
        paths = [path_1, path_2]

        navigator = n.Navigator(page_size=page_size)
        for path in paths:
            root, _ = create_get_files_tree_func(root_path=path)
            navigator.add_files_tree(root, path)

        navigator.set_parent_dir()
        self.assertEqual(navigator.current_dir.name, "/")

    def test_pagination(self):
        page_size = 7
        path_1 = "path_1"
        path_2 = "path_2"
        dirs_num = 5
        file_num = 5
        depth = 2
        paths = [path_1, path_2]

        navigator = n.Navigator(page_size=page_size)
        for path in paths:
            root, _ = create_get_files_tree_func(
                root_path=path,
                dirs_num=dirs_num,
                files_num=file_num,
                depth=depth)
            navigator.add_files_tree(root, path)

        self.assertEqual(navigator.pagination.total_size, 2)
        navigator.set_dir(path_1)
        self.assertEqual(navigator.pagination.total_size, (dirs_num + file_num))
        navigator.set_parent_dir()
        self.assertEqual(navigator.pagination.total_size, 2)

    def test_get_file(self):
        page_size = 7
        path_1 = "path_1"
        path_2 = "path_2"
        paths = [path_1, path_2]

        navigator = n.Navigator(page_size=page_size)
        for path in paths:
            root, _ = create_get_files_tree_func(root_path=path)
            navigator.add_files_tree(root, path)

        navigator.set_dir(path_1)
        file = navigator.get_file("file_1")
        self.assertEqual(file.name, "file_1")
