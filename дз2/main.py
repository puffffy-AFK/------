import subprocess
import os
from typing import Dict, Set


class DependencyVisualizer:
    def __init__(self, package_name: str, max_depth: int, plantuml_path: str):
        self.package_name = package_name
        self.max_depth = max_depth
        self.plantuml_path = plantuml_path
        self.dependencies = {}  # type: Dict[str, Set[str]]

    def get_dependencies(self, package: str, depth: int = 0) -> Set[str]:
        """Рекурсивный сбор зависимостей для пакета."""
        if depth >= self.max_depth:
            return set()

        if package in self.dependencies:
            return self.dependencies[package]

        print(f"Получаем зависимости для пакета {package}...")
        result = subprocess.run(['apk', 'info', '-R', package], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка при выполнении команды для пакета {package}: {result.stderr}")
            return set()

        dependencies = set()
        for line in result.stdout.splitlines():
            line = line.strip()

            # Игнорируем пустые строки и строки, начинающиеся с пути
            if line and "depends on:" not in line and not line.startswith('/'):
                # Удаляем префикс 'so:' и отбрасываем версию библиотеки
                if line.startswith("so:"):
                    line = line[3:].split('.')[0]
                elif '>=' in line:
                    # Убираем версию, если указано "libname>=version"
                    line = line.split('>=')[0].strip()
                dependencies.add(line)

        print(f"Найденные зависимости для {package}: {dependencies}")
        self.dependencies[package] = dependencies

        # Рекурсивно получаем зависимости для каждого пакета
        dependencies_copy = self.dependencies[package].copy()
        for dep in dependencies_copy:
            self.dependencies[package].update(self.get_dependencies(dep, depth + 1))

        return self.dependencies[package]

    def generate_puml_tree(self, package: str, depth: int = 0, visited: Set[str] = None) -> str:
        """Рекурсивно генерирует PlantUML-код для отображения дерева зависимостей."""
        if visited is None:
            visited = set()

        if package in visited:
            return ""  # Избегаем циклических зависимостей
        visited.add(package)

        puml_code = ""
        if depth == 0:
            puml_code += f'[{package}]\n'  # Корневой узел

        # Если пакет уже в словаре зависимостей, обрабатываем его зависимости
        if package in self.dependencies:
            for dependency in self.dependencies[package]:
                puml_code += f"[{package}] --> [{dependency}]\n"
                puml_code += self.generate_puml_tree(dependency, depth + 1, visited)

        return puml_code

    def visualize(self):
        """Визуализация графа зависимостей с помощью PlantUML."""
        puml_code = self.generate_puml_tree(self.package_name)
        with open("output.puml", "w") as f:
            f.write(f"@startuml\n{puml_code}@enduml")

        subprocess.run(['java', '-jar', self.plantuml_path, "output.puml"])
        os.remove("output.puml")


def main():
    plantuml_path = input("Введите путь к plantuml.jar: ").strip()
    package_name = input("Введите имя пакета Alpine Linux для анализа зависимостей: ").strip()

    while True:
        try:
            max_depth = int(input("Введите максимальную глубину анализа зависимостей (например, 2): ").strip())
            break
        except ValueError:
            print("Пожалуйста, введите корректное целое число для глубины.")

    visualizer = DependencyVisualizer(package_name, max_depth, plantuml_path)
    visualizer.get_dependencies(package_name)
    visualizer.visualize()
    print("Граф зависимостей успешно создан и визуализирован.")


if __name__ == "__main__":
    main()
