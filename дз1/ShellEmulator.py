import os
import sys
import configparser
from pathlib import Path
import rarfile



def handle_ls(current_dir):
    return os.listdir(current_dir)


def handle_cd(command, current_dir):
    try:
        if command.strip() == "cd":
            raise ValueError("Команда cd требует аргумент: название директории.")

        _, dir_name = command.split()

        if dir_name == "..":
            return os.path.dirname(current_dir)

        new_dir = os.path.join(current_dir, dir_name)

        if os.path.isdir(new_dir):
            return new_dir
        else:
            parent_dir = os.path.dirname(current_dir)
            new_dir = os.path.join(parent_dir, dir_name)

            if os.path.isdir(new_dir):
                return new_dir
            else:
                raise FileNotFoundError(f"Директория {dir_name} не найдена.")
    except ValueError:
        raise ValueError("Команда cd требует аргумент: название директории.")


def handle_pwd(current_dir):
    return current_dir


def handle_mv(command, current_dir):
    try:
        _, src, dest = command.split()
        src_path = os.path.join(current_dir, src)
        dest_path = os.path.join(current_dir, dest)
        if os.path.exists(src_path):
            os.rename(src_path, dest_path)
        else:
            raise FileNotFoundError(f"Файл {src} не найден.")
    except ValueError:
        raise ValueError("Команда mv требует два аргумента: исходный и целевой файлы.")


def handle_tree(current_dir):
    tree_structure = ""
    for root, dirs, files in os.walk(current_dir):
        indent = ' ' * 4 * (root.count(os.sep) - current_dir.count(os.sep))
        tree_structure += f"{indent}{os.path.basename(root)}/\n"
        for file in files:
            tree_structure += f"{indent}    {file}\n"
    return tree_structure


def shell_emulator(user, fs_archive, log_file, startup_script=None):
    extract_path = Path("C:/tmp/virtual_fs").as_posix()
    os.makedirs(extract_path, exist_ok=True)  # Создаем путь, если его нет

    if fs_archive.endswith('.rar'):
        with rarfile.RarFile(fs_archive) as archive:
            archive.extractall(extract_path)
    else:
        print("Ошибка: Поддерживается только формат .rar.")
        sys.exit(1)

    current_dir = extract_path
    log_data = []

    print(f"Текущая директория: {current_dir}")

    while True:
        command = input(f"{user}:{current_dir}$ ")
        if command == "exit":
            break
        current_dir = process_command(command, user, current_dir, log_data)

def process_command(command, user, current_dir, log_data):
    try:
        if command.startswith("ls"):
            output = handle_ls(current_dir)
            print("\n".join(output))
        elif command.startswith("cd"):
            current_dir = handle_cd(command, current_dir)
            output = current_dir
        elif command.startswith("pwd"):
            output = handle_pwd(current_dir)
            print(output)
        elif command.startswith("mv"):
            handle_mv(command, current_dir)
            output = "Файл перемещен."
        elif command.startswith("tree"):
            output = handle_tree(current_dir)
            print(output)
        else:
            output = "Неизвестная команда."
            print(output)

        log_data.append([user, command, output])
        return current_dir
    except Exception as e:
        print(f"Ошибка: {e}")
        log_data.append([user, command, str(e)])
        return current_dir


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    user = config.get("ShellEmulator", "user")
    fs_archive = config.get("ShellEmulator", "fs_archive")
    log_file = config.get("ShellEmulator", "log_file")
    startup_script = config.get("ShellEmulator", "startup_script")

    shell_emulator(user, fs_archive, log_file, startup_script)
