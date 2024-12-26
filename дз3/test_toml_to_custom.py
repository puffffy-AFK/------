import unittest
import subprocess
import sys

class TestTomlToCustom(unittest.TestCase):
    def setUp(self):
        self.script = 'toml_to_custom.py'
        self.maxDiff = None  # Для полного отображения различий в больших строках

    def run_script(self, input_text):
        """Запускает скрипт с предоставленным входным текстом и захватывает вывод."""
        process = subprocess.Popen(
            [sys.executable, self.script],  # Используем sys.executable для правильного интерпретатора
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate(input_text)
        return stdout.strip(), stderr.strip(), process.returncode

    def test_basic_conversion(self):
        input_toml = '''
[server]
host = "localhost"
port = 8080
'''
        expected_output = '''[
  server:
    host => "localhost",
    port => 8080,
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_nested_dictionaries(self):
        input_toml = '''
[parent]
[parent.child]
name = "child_name"
'''
        expected_output = '''[
  parent:
    child:
      name => "child_name",
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_constants(self):
        input_toml = '''
let x = 10
let y = 20

[values]
a = "|x + y|"
b = "|max(x, y)|"
'''
        expected_output = '''[
  values:
    a => 30,
    b => 20,
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_multi_line_comment(self):
        input_toml = '''
{-
Это многострочный
комментарий
-}

[data]
value = 42
'''
        expected_output = '''[
  data:
    value => 42,
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_invalid_identifier(self):
        input_toml = '''
[data]
123invalid = "test"
'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertNotEqual(returncode, 0)
        self.assertIn("Ошибка: Некорректное имя '123invalid'", stderr)

    def test_unsupported_value_type(self):
        input_toml = '''
[data]
value = true
'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertNotEqual(returncode, 0)
        self.assertIn("Ошибка: Неподдерживаемый тип значения 'True'.", stderr)

    def test_list_values(self):
        input_toml = '''
[data]
items = [1, 2, 3]
'''
        expected_output = '''[
  data:
    items => [
      1,
      2,
      3,
    ],
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_expression_errors(self):
        input_toml = '''
let x = 10

[data]
value = "|x - y|"
'''
        # Здесь y не определена, должно вызвать ошибку
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertNotEqual(returncode, 0)
        self.assertIn("Неизвестная переменная 'y'", stderr)

    def test_missing_constants(self):
        input_toml = '''
[data]
value = "|unknown + 1|"
'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertNotEqual(returncode, 0)
        self.assertIn("Неизвестная переменная 'unknown'", stderr)

    def test_operations(self):
        input_toml = '''
let a = 5
let b = 3

[calculations]
sum = "|a + b|"
difference = "|a - b|"
max_value = "|max(a, b)|"
'''
        expected_output = '''[
  calculations:
    sum => 8,
    difference => 2,
    max_value => 5,
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_floating_point_numbers(self):
        input_toml = '''
[data]
value = 3.14
'''
        expected_output = '''[
  data:
    value => 3.14,
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_list_of_dictionaries(self):
        input_toml = '''
[data]
items = [
    {name = "item1", value = 10},
    {name = "item2", value = 20}
]
'''
        expected_output = '''[
  data:
    items => [
      [
        name => "item1",
        value => 10,
      ],
      [
        name => "item2",
        value => 20,
      ],
    ],
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

    def test_complex_expression(self):
        input_toml = '''
let x = 5
let y = 15

[calc]
result = "|max(x + 10, y)|"
'''
        expected_output = '''[
  calc:
    result => 15,
]'''
        stdout, stderr, returncode = self.run_script(input_toml)
        self.assertEqual(returncode, 0, msg=stderr)
        self.assertEqual(stdout, expected_output)

if __name__ == '__main__':
    unittest.main()
