import unittest
from unittest.mock import patch, mock_open
from main import DependencyVisualizer
import os


class TestDependencyVisualizer(unittest.TestCase):

    @patch("subprocess.run")
    def test_get_dependencies_no_dependencies(self, mock_subprocess_run):
        # Заглушка для команды `apk info -R`
        mock_subprocess_run.return_value.stdout = ""
        mock_subprocess_run.return_value.returncode = 0

        visualizer = DependencyVisualizer("testpkg", max_depth=2, plantuml_path="/path/to/plantuml.jar")
        dependencies = visualizer.get_dependencies("testpkg")

        self.assertEqual(dependencies, set(), "Если нет зависимостей, должен вернуться пустой набор.")

    @patch("subprocess.run")
    def test_get_dependencies_with_dependencies(self, mock_subprocess_run):
        # Заглушка для команды `apk info -R`
        mock_subprocess_run.side_effect = [
            unittest.mock.Mock(stdout="depends on:\nlibA\nlibB", returncode=0),
            unittest.mock.Mock(stdout="depends on:\nlibC", returncode=0),  # Для libA
            unittest.mock.Mock(stdout="depends on:\n", returncode=0)       # Для libB
        ]

        visualizer = DependencyVisualizer("testpkg", max_depth=2, plantuml_path="/path/to/plantuml.jar")
        dependencies = visualizer.get_dependencies("testpkg")

        expected = {"libA", "libB", "libC"}
        self.assertEqual(dependencies, expected, "Должны корректно возвращаться все зависимости.")

    def test_generate_puml_tree_no_dependencies(self):
        visualizer = DependencyVisualizer("testpkg", max_depth=2, plantuml_path="/path/to/plantuml.jar")
        visualizer.dependencies = {"testpkg": set()}  # Имитируем отсутствие зависимостей

        puml_code = visualizer.generate_puml_tree("testpkg")
        self.assertEqual(puml_code.strip(), "[testpkg]", "Код PUML должен содержать только корневой узел.")

    def test_generate_puml_tree_with_dependencies(self):
        visualizer = DependencyVisualizer("testpkg", max_depth=2, plantuml_path="/path/to/plantuml.jar")
        visualizer.dependencies = {
            "testpkg": {"libA", "libB"},
            "libA": {"libC"},
            "libB": set(),
            "libC": set(),
        }

        puml_code = visualizer.generate_puml_tree("testpkg")

        expected = """[testpkg]
[testpkg] --> [libA]
[testpkg] --> [libB]
[libA] --> [libC]
"""
        self.assertEqual(
            set(puml_code.strip().splitlines()),
            set(expected.strip().splitlines()),
            "Код PUML должен корректно отображать зависимости."
        )

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_visualize(self, mock_open_file, mock_subprocess_run):
        visualizer = DependencyVisualizer("testpkg", max_depth=2, plantuml_path="/path/to/plantuml.jar")
        visualizer.dependencies = {"testpkg": {"libA"}, "libA": set()}

        # Имитация существования файла
        with patch("os.remove") as mock_remove:
            visualizer.visualize()

            # Проверяем, что файл output.puml был записан
            mock_open_file.assert_called_once_with("output.puml", "w")
            handle = mock_open_file()
            handle.write.assert_called_once()

            # Проверяем, что вызван subprocess.run для PlantUML
            mock_subprocess_run.assert_called_once_with(['java', '-jar', '/path/to/plantuml.jar', "output.puml"])

            # Проверяем, что файл удалён
            mock_remove.assert_called_once_with("output.puml")

        if __name__ == "__main__":
            unittest.main()