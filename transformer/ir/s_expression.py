from typing import List


# 基础原子对象
class Atom:
    pass


# 代表可以直接用字符串形式存储的原子对象，包括BooleanLiteral、NULL、NumberLiteral、StringLiteral、COUNT(*)和Parameter
class LiteralString(Atom):
    def __init__(self, literal_string: str):
        self.literal_string = literal_string

    def __str__(self):
        return self.literal_string


class ListLiteral(Atom):
    # 注意：该处expressions为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, expressions: List):
        self.expressions = expressions


class MapLiteral(Atom):
    # 注意：该处key_values为dict[str, Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, keys_values: dict):
        self.keys_values = keys_values


class CaseExpression(Atom):
    pass


class ListComprehension(Atom):
    pass


class PatternComprehension(Atom):
    pass


class ParenthesizedExpression(Atom):
    # 注意：该处expression为Expression类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, expression):
        self.expression = expression


class FunctionInvocation(Atom):
    # 注意：该处expressions为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, function_name: str, is_distinct=False, expressions: List = None):
        self.function_name = function_name
        self.is_distinct = is_distinct
        if expressions is None:
            expressions = []
        self.expressions = expressions


class ExistentialSubquery(Atom):
    pass


class PropertiesLabelsExpression:
    def __init__(self, atom: Atom, property_chains: List[str] = None, labels: List[str] = None):
        self.atom = atom
        if property_chains is None:
            property_chains = []
        self.property_chains = property_chains
        if labels is None:
            labels = []
        self.labels = labels


class AtTExpression:
    def __init__(self, atom: Atom, property_chains: List[str] = None, is_value: bool = False,
                 time_property_chains: List[str] = None):
        self.atom = atom
        if property_chains is None:
            property_chains = []
        # 获取属性节点的有效时间
        self.property_chains = property_chains
        # 获取值节点的有效时间
        self.is_value = is_value
        # 获取有效时间的属性
        if time_property_chains is None:
            time_property_chains = []
        self.time_property_chains = time_property_chains


class ListIndexExpression:
    # 注意：该处index_expression为Expression类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, principal_expression: PropertiesLabelsExpression | AtTExpression, is_positive=True,
                 index_expression=None):
        self.principal_expression = principal_expression
        # 是否为正
        self.is_positive = is_positive
        # 列表索引
        self.index_expression = index_expression


class PowerExpression:
    def __init__(self, list_index_expressions: List[ListIndexExpression]):
        self.list_index_expressions = list_index_expressions


class MultiplyDivideExpression:
    def __init__(self, left_expression: PowerExpression, multiply_divide_operation: str = None,
                 right_expression: PowerExpression = None):
        if multiply_divide_operation not in ['*', '/']:
            raise ValueError("The multiply_divide_operation must in '*' and '/'.")
        self.left_expression = left_expression
        self.multiply_divide_operation = multiply_divide_operation
        self.right_expression = right_expression


class AddSubtractExpression:
    def __init__(self, left_expression: MultiplyDivideExpression, add_subtract_operation: str = None,
                 right_expression: MultiplyDivideExpression = None):
        if add_subtract_operation not in ['-', '+']:
            raise ValueError("The add_subtract_operation must in '-' and '+'.")
        self.left_expression = left_expression
        self.add_subtract_operation = add_subtract_operation
        self.right_expression = right_expression


class TimePredicateExpression:
    def __init__(self, time_operation: str, add_or_subtract_expression: AddSubtractExpression = None):
        if time_operation.lower() not in ['during', 'overlaps']:
            raise ValueError("The time operation must in 'during' and 'overlaps'.")
        self.time_operation = time_operation
        self.add_or_subtract_expression = add_or_subtract_expression


class StringPredicateExpression:
    def __init__(self, string_operation: str, add_or_subtract_expression: AddSubtractExpression = None):
        if string_operation.lower() not in ['starts with', 'ends with', 'contains']:
            raise ValueError("The string operation must in 'starts with', 'ends with' and 'contains'.")
        self.string_operation = string_operation
        self.add_or_subtract_expression = add_or_subtract_expression


class ListPredicateExpression:
    def __init__(self, add_or_subtract_expression: AddSubtractExpression = None):
        self.add_or_subtract_expression = add_or_subtract_expression


class NullPredicateExpression:
    def __init__(self, is_null: bool = True):
        # is_null为True表示IS NULL操作，反之表示IS NOT NULL操作
        self.is_null = is_null


class SubjectExpression:
    def __init__(self, add_or_subtract_expression: AddSubtractExpression,
                 predicate_expression: TimePredicateExpression | StringPredicateExpression | ListPredicateExpression | NullPredicateExpression = None):
        self.add_or_subtract_expression = add_or_subtract_expression
        self.predicate_expression = predicate_expression


class ComparisonExpression:
    def __init__(self, left_expression: SubjectExpression, comparison_operation: str = None,
                 right_expression: SubjectExpression = None):
        if comparison_operation not in ['=', '<>', '<', '>', '<=', '>=']:
            raise ValueError("The comparison operation must in '=', '<>', '<', '>', '<=', '>='.")
        self.left_expression = left_expression
        self.comparison_operation = comparison_operation
        self.right_expression = right_expression


class NotExpression:
    def __init__(self, comparison_expression: ComparisonExpression, is_not=False):
        self.comparison_expression = comparison_expression
        self.is_not = is_not


class AndExpression:
    def __init__(self, not_expressions: List[NotExpression]):
        self.not_expressions = not_expressions


class XorExpression:
    def __init__(self, and_expressions: List[AndExpression]):
        self.and_expressions = and_expressions


class OrExpression:
    def __init__(self, xor_expressions: List[XorExpression]):
        self.xor_expressions = xor_expressions


class Expression:
    def __init__(self, or_expression):
        self.or_expression = or_expression
