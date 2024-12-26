import sys
import toml
import re
import ast

# Регулярные выражения для синтаксических элементов
IDENTIFIER_REGEX = r"^[_a-z]+$"
MULTILINE_COMMENT_REGEX = r"\{\-.*?\-\}"

class SafeEvaluator(ast.NodeVisitor):
    """Безопасный вычислитель выражений."""
    allowed_nodes = {
        ast.Expression, ast.BinOp, ast.Constant, ast.Add, ast.Sub, ast.Call,
        ast.Name, ast.Load
    }

    def __init__(self, variables):
        self.variables = variables
        self.allowed_names = {'max': max}

    def visit(self, node):
        if type(node) not in self.allowed_nodes:
            raise ValueError(f"Недопустимое выражение: {ast.dump(node)}")
        return super().visit(node)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        else:
            raise ValueError(f"Недопустимая операция: {type(node.op).__name__}()")

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        else:
            raise ValueError(f"Недопустимое значение: {node.value}")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.allowed_names:
            args = [self.visit(arg) for arg in node.args]
            return self.allowed_names[node.func.id](*args)
        else:
            raise ValueError(f"Недопустимая функция: {ast.dump(node.func)}")

    def visit_Name(self, node):
        if node.id in self.variables:
            return self.variables[node.id]
        else:
            raise ValueError(f"Неизвестная переменная '{node.id}'")

class ConfigProcessor:
    def __init__(self):
        self.constants = {}

    def parse_toml(self, toml_data):
        """Парсит TOML и преобразует в пользовательский формат."""
        if not isinstance(toml_data, dict):
            raise ValueError("Ошибка: Входные данные должны быть словарем.")
        return self.process_dict(toml_data)

    def process_dict(self, data, depth=0):
        """Обрабатывает словарь и преобразует его в нужный формат."""
        result = []
        indent = "  " * depth

        # Добавляем '[' только на верхнем уровне
        if depth == 0:
            result.append(f"{indent}[")

        for key, value in data.items():
            key = key.strip()
            if not re.match(IDENTIFIER_REGEX, key):
                raise ValueError(f"Ошибка: Некорректное имя '{key}'.")

            if isinstance(value, dict):
                result.append(f"{indent}  {key}:")
                # Рекурсивно обрабатываем вложенный словарь без добавления дополнительных скобок
                result.extend(self.process_dict(value, depth + 1))
            elif isinstance(value, list):
                result.append(f"{indent}  {key} => [")
                for item in value:
                    if isinstance(item, (int, float, str)):
                        result.append(f"{indent}    {self.format_value(item)},")
                    elif isinstance(item, dict):
                        result.append(f"{indent}    [")
                        # Передаем depth +2 для корректной индентации вложенных словарей
                        result.extend(self.process_dict(item, depth + 2))
                        result.append(f"{indent}    ],")
                    else:
                        raise ValueError(f"Ошибка: Неподдерживаемый тип в списке '{item}'.")
                result.append(f"{indent}  ],")
            else:
                if isinstance(value, str) and self.is_constant_expression(value):
                    evaluated_value = self.evaluate_expression(value)
                    result.append(f"{indent}  {key} => {self.format_value(evaluated_value)},")
                else:
                    result.append(f"{indent}  {key} => {self.format_value(value)},")
        # Добавляем закрывающую скобку ']' только на верхнем уровне
        if depth == 0:
            result.append(f"{indent}]")
        return result

    def format_value(self, value):
        """Форматирует значения (строки, числа, словари)."""
        if isinstance(value, bool):
            raise ValueError(f"Ошибка: Неподдерживаемый тип значения '{value}'.")
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            raise ValueError(f"Ошибка: Неподдерживаемый тип значения '{value}'.")

    def is_constant_expression(self, value):
        """Проверяет, является ли строка константным выражением в | |."""
        return isinstance(value, str) and value.startswith('|') and value.endswith('|')

    def evaluate_expression(self, expr):
        """Вычисляет выражение на этапе трансляции."""
        expr_content = expr.strip("|")
        try:
            # Парсим выражение
            node = ast.parse(expr_content, mode='eval')
            evaluator = SafeEvaluator(self.constants)
            return evaluator.visit(node.body)
        except Exception as e:
            raise ValueError(f"{e}")

    def process_multiline_comments(self, text):
        """Удаляет многострочные комментарии из текста."""
        return re.sub(MULTILINE_COMMENT_REGEX, '', text, flags=re.DOTALL)

    def process_let_statements(self, text):
        """Обрабатывает объявления констант и сохраняет их."""
        let_pattern = re.compile(r"let\s+([_a-z]+)\s*=\s*(.+)")
        lines = text.replace('\r\n', '\n').split('\n')
        new_lines = []
        for line in lines:
            match = let_pattern.match(line.strip())
            if match:
                name, value = match.groups()
                if not re.match(IDENTIFIER_REGEX, name):
                    raise ValueError(f"Ошибка: Некорректное имя константы '{name}'.")
                if self.is_constant_expression(value.strip()):
                    evaluated_value = self.evaluate_expression(value.strip())
                else:
                    evaluated_value = self.parse_value(value.strip())
                self.constants[name] = evaluated_value
            else:
                new_lines.append(line)
        return '\n'.join(new_lines)

    def parse_value(self, value):
        """Парсит значение из строки в соответствующий тип."""
        value = value.strip()
        if value.isdigit():
            return int(value)
        elif re.match(r'^-?\d+(\.\d+)?$', value):
            return float(value)
        elif value.startswith('"') and value.endswith('"'):
            return value.strip('"')
        else:
            raise ValueError(f"Ошибка: Не удалось распознать значение '{value}'.")

def main():
    processor = ConfigProcessor()

    try:
        toml_input = sys.stdin.read()
        # Удаляем многострочные комментарии
        toml_input = processor.process_multiline_comments(toml_input)

        # Обрабатываем объявления констант
        toml_input = processor.process_let_statements(toml_input)

        # Парсим TOML
        toml_data = toml.loads(toml_input)

        # Преобразуем в пользовательский формат
        custom_config = processor.parse_toml(toml_data)

        # Выводим результат
        for line in custom_config:
            print(line)

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
