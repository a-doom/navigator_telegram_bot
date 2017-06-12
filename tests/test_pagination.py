import unittest
import navigator as n
import math


def create_dir(dirs_num = 3, files_num = 3):
    root_dir = n.File("test_1", None, True)
    for i in range(dirs_num):
        filename = "dir_{0}".format(i)
        dir = n.File(filename, root_dir, True)
        root_dir.dirs.append(dir)
    for i in range(files_num):
        filename = "file_{0}".format(i)
        file = n.File(filename, root_dir, False)
        root_dir.files.append(file)
    return root_dir


class TestPagination(unittest.TestCase):
    def test_init_1(self):
        dirs_num = 10
        file_num = 15
        page_size = 7
        f = create_dir(dirs_num, file_num)

        result = n.Pagination(f, page_size)
        self.assertEqual(len(result.files), file_num)
        self.assertEqual(len(result.dirs), dirs_num)
        self.assertEqual(len(result.all_objects), dirs_num + file_num)
        self.assertEqual(result.page_size, page_size)
        self.assertEqual(result.total_pages_num, math.ceil((dirs_num + file_num) / page_size))

    def test_init_2(self):
        dirs_num = 0
        file_num = 15
        page_size = 7
        f = create_dir(dirs_num, file_num)

        result = n.Pagination(f, page_size)
        self.assertEqual(len(result.files), file_num)
        self.assertEqual(len(result.dirs), dirs_num)
        self.assertEqual(len(result.all_objects), dirs_num + file_num)
        self.assertEqual(result.page_size, page_size)
        self.assertEqual(result.total_pages_num, math.ceil((dirs_num + file_num) / page_size))

    def test_init_3(self):
        dirs_num = 0
        file_num = 0
        page_size = 7
        f = create_dir(dirs_num, file_num)

        result = n.Pagination(f, page_size)
        self.assertEqual(len(result.files), file_num)
        self.assertEqual(len(result.dirs), dirs_num)
        self.assertEqual(len(result.all_objects), dirs_num + file_num)
        self.assertEqual(result.page_size, page_size)
        self.assertEqual(result.total_pages_num, math.ceil((dirs_num + file_num) / page_size))

    def test_set_page_1(self):
        dirs_num = 10
        file_num = 15
        page_size = 7
        f = create_dir(dirs_num, file_num)

        p = n.Pagination(f, page_size)
        p.set_page(99)
        self.assertEqual(p.current_page_num, 4)

    def test_set_page_2(self):
        dirs_num = 10
        file_num = 15
        page_size = 7
        f = create_dir(dirs_num, file_num)

        p = n.Pagination(f, page_size)
        p.set_page(2)
        self.assertEqual(p.current_page_num, 2)

    def test_set_first_page(self):
        dirs_num = 10
        file_num = 15
        page_size = 7
        f = create_dir(dirs_num, file_num)

        p = n.Pagination(f, page_size)
        p.set_page(3)
        p.set_first_page()
        p.set_prev_page()
        p.set_first_page()
        self.assertEqual(p.current_page_num, 1)
        self.assertTrue(p.is_first_page())

    def test_set_last_page(self):
        dirs_num = 5
        file_num = 5
        page_size = 2
        f = create_dir(dirs_num, file_num)

        p = n.Pagination(f, page_size)
        p.set_last_page()
        p.set_next_page()
        p.set_last_page()
        self.assertEqual(p.current_page_num, 5)
        self.assertTrue(p.is_last_page())

    def test_get_file_1(self):
        dirs_num = 10
        file_num = 0
        page_size = 2
        f = create_dir(dirs_num, file_num)

        p = n.Pagination(f, page_size)
        f = p.get_file(0)
        self.assertEqual(f.name, "dir_0")
        f = p.get_file(1)
        self.assertEqual(f.name, "dir_1")
        f = p.get_file(2)
        self.assertIsNone(f)

    def test_get_file_2(self):
        dirs_num = 0
        file_num = 10
        page_size = 2
        f = create_dir(dirs_num, file_num)

        p = n.Pagination(f, page_size)
        p.set_page(3)
        f = p.get_file(0)
        self.assertEqual(f.name, "file_4")
