import pytest
import os
from ShellEmulator import handle_ls, handle_cd, handle_pwd, handle_mv, handle_tree

def test_handle_ls(tmpdir):
    test_dir = tmpdir.mkdir("test")
    test_dir.join("file1.txt").write("content1")
    test_dir.join("file2.txt").write("content2")
    files = handle_ls(str(test_dir))
    assert sorted(files) == ["file1.txt", "file2.txt"]

def test_handle_cd(tmpdir):
    test_dir = tmpdir.mkdir("test")
    sub_dir = test_dir.mkdir("subdir")
    current_dir = str(test_dir)
    command = f"cd {sub_dir.basename}"
    updated_dir = handle_cd(command, current_dir)
    assert updated_dir == str(sub_dir)

def test_handle_pwd(tmpdir):
    test_dir = tmpdir.mkdir("test")
    current_dir = str(test_dir)
    assert handle_pwd(current_dir) == current_dir

def test_handle_mv(tmpdir):
    test_dir = tmpdir.mkdir("test")
    src_file = test_dir.join("file1.txt")
    src_file.write("content")
    dest_file = test_dir.join("file2.txt")
    handle_mv(f"mv {src_file.basename} {dest_file.basename}", str(test_dir))
    assert os.path.exists(dest_file)
    assert not os.path.exists(src_file)

def test_handle_tree(tmpdir):
    root = tmpdir.mkdir("root")
    root.mkdir("subdir").join("file.txt").write("content")
    tree_output = handle_tree(str(root))
    assert "subdir/" in tree_output
    assert "file.txt" in tree_output
