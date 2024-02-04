from typing import List

from transformer.exceptions.s_exception import TranslateError


class ListLiteral:
    # 注意：该处expressions为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, expressions: List):
        self.expressions = expressions


class MapLiteral:
    # 注意：该处key_values为dict[str, Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, keys_values: dict):
        self.keys_values = keys_values


class CaseExpression:
    # 注意：该处expression为Expression类型，conditions和results为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, expression=None, conditions: List = None, results: List = None):
        if conditions is None or results is None:
            raise TranslateError("The conditions and reaults can't be None")
        if len(conditions) not in [len(results), len(results) - 1]:
            raise TranslateError("The quantity of conditions and results can't match")
        self.expression = expression
        self.conditions = conditions
        self.results = results


class ListComprehension:
    # 注意：该处list_expression,where_expression和back_expression为Expression类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, variable: str, list_expression, where_expression=None, back_expression=None):
        self.variable = variable
        self.list_expression = list_expression
        self.where_expression = where_expression
        self.back_expression = back_expression


class PatternComprehension:
    pass


class Quantifier:
    pass


class PatternPredicate:
    pass


class ParenthesizedExpression:
    # 注意：该处expression为Expression类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, expression):
        self.expression = expression


class FunctionInvocation:
    # 注意：该处expressions为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, function_name: str, is_distinct=False, expressions: List = None):
        self.function_name = function_name
        self.is_distinct = is_distinct
        # 输入参数
        if expressions is None:
            expressions = []
        self.expressions = expressions


class ExistentialSubquery:
    pass


# 基础原子对象
class Atom:
    def __init__(self,
                 particle: str | ListLiteral | MapLiteral | CaseExpression | ListComprehension | PatternComprehension | Quantifier | PatternPredicate | ParenthesizedExpression | FunctionInvocation | ExistentialSubquery):
        # BooleanLiteral、NULL、NumberLiteral、StringLiteral、COUNT(*)和Parameter类型可以直接用str存储
        self.particle = particle


class TimePointLiteral:
    def __init__(self, time_point: str | MapLiteral):
        self.time_point = time_point


class AtTElement:
    def __init__(self, interval_from: TimePointLiteral, interval_to: TimePointLiteral = None):
        self.interval_from = interval_from
        self.interval_to = interval_to


class PropertiesLabelsExpression:
    def __init__(self, atom: Atom, property_chains: List[str] = None, labels_poundT: List[str] | AtTElement = None):
        self.atom = atom
        if property_chains is None:
            property_chains = []
        self.property_chains = property_chains
        if labels_poundT is None:
            labels_poundT = []
        self.labels_poundT = labels_poundT


class PoundTExpression:
    def __init__(self, atom: Atom, property_chains: List[str] = None, property_name: str = None,
                 time_window: bool | AtTElement = None, time_property_chains: List[str] = None):
        self.atom = atom
        if property_chains is None:
            property_chains = []
        if property_name is None and len(property_chains) > 0:
            property_name = property_chains[-1]
            property_chains.pop(-1)
        self.property_chains = property_chains
        self.property_name = property_name
        # #Value表示获取所有值节点的有效时间，传入True；@T表示获取该时间窗口下的值节点的有效时间，传入时间区间/时间点
        self.time_window = time_window
        # 获取有效时间的属性
        if time_property_chains is None:
            time_property_chains = []
        self.time_property_chains = time_property_chains


class IndexExpression:
    # 注意：该处left_expression和right_expression为Expression类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, left_expression, right_expression=None):
        self.left_expression = left_expression
        self.right_expression = right_expression


# 合并了oC_UnaryAddOrSubtractExpression和oC_ListOperatorExpression
class ListIndexExpression:
    def __init__(self, principal_expression: PropertiesLabelsExpression | PoundTExpression, is_positive=True,
                 index_expressions: List[IndexExpression] = None):
        self.principal_expression = principal_expression
        # 是否为正
        self.is_positive = is_positive
        # 列表索引
        if index_expressions is None:
            index_expressions = []
        self.index_expressions = index_expressions


class PowerExpression:
    def __init__(self, list_index_expressions: List[ListIndexExpression]):
        self.list_index_expressions = list_index_expressions


class MultiplyDivideModuloExpression:
    def __init__(self, power_expressions: List[PowerExpression], multiply_divide_modulo_operations: List[str] = None):
        self.power_expressions = power_expressions
        if multiply_divide_modulo_operations is None:
            multiply_divide_modulo_operations = []
        if len(power_expressions) != len(multiply_divide_modulo_operations) + 1:
            raise TranslateError(
                "The numbers of the power expressions and multiply/divide/modulo operations are not matched")
        for multiply_divide_modulo_operation in multiply_divide_modulo_operations:
            if multiply_divide_modulo_operation not in ['*', '/', '%']:
                raise TranslateError("The multiply/divide/modulo operation must be '*', '/' or '%'")
        self.multiply_divide_modulo_operations = multiply_divide_modulo_operations


class AddSubtractExpression:
    def __init__(self, multiply_divide_modulo_expressions: List[MultiplyDivideModuloExpression],
                 add_subtract_operations: List[str] = None):
        self.multiply_divide_modulo_expressions = multiply_divide_modulo_expressions
        if add_subtract_operations is None:
            add_subtract_operations = []
        if len(multiply_divide_modulo_expressions) != len(add_subtract_operations) + 1:
            raise TranslateError(
                "The numbers of the multiply/divide/modulo expressions and add/subtract operations are not matched")
        for add_subtract_operation in add_subtract_operations:
            if add_subtract_operation not in ['-', '+']:
                raise TranslateError("The add/subtract operation must be '+' or '-'")
        self.add_subtract_operations = add_subtract_operations


class TimePredicateExpression:
    def __init__(self, time_operation: str, add_subtract_expression: AddSubtractExpression):
        if time_operation.lower() not in ["during", "overlaps"]:
            raise TranslateError("The time operation must be 'during' or 'overlaps'")
        self.time_operation = time_operation
        self.add_subtract_expression = add_subtract_expression


class StringPredicateExpression:
    def __init__(self, string_operation: str, add_subtract_expression: AddSubtractExpression):
        if string_operation.lower() not in ["starts with", "ends with", "contains"]:
            raise TranslateError("The string operation must in 'starts with', 'ends with' and 'contains'")
        self.string_operation = string_operation
        self.add_subtract_expression = add_subtract_expression


class ListPredicateExpression:
    def __init__(self, add_subtract_expression: AddSubtractExpression):
        self.add_subtract_expression = add_subtract_expression


class NullPredicateExpression:
    def __init__(self, is_null: bool = True):
        # is_null为True表示IS NULL操作，反之表示IS NOT NULL操作
        self.is_null = is_null


# 相当于StringListNullPredicateExpression
class SubjectExpression:
    def __init__(self, add_subtract_expression: AddSubtractExpression,
                 predicate_expression: TimePredicateExpression | StringPredicateExpression | ListPredicateExpression | NullPredicateExpression = None):
        self.add_or_subtract_expression = add_subtract_expression
        self.predicate_expression = predicate_expression


class ComparisonExpression:
    def __init__(self, subject_expressions: List[SubjectExpression], comparison_operations: List[str] = None):
        self.subject_expressions = subject_expressions
        if comparison_operations is None:
            comparison_operations = []
        if len(subject_expressions) != len(comparison_operations) + 1:
            raise TranslateError("The numbers of the subject expressions and comparison operations are not matched")
        for comparison_operation in comparison_operations:
            if comparison_operation not in ['=', "<>", '<', '>', "<=", ">="]:
                raise TranslateError("The comparison operation must be '=', '<>', '<', '>', '<=' or '>='")
        self.comparison_operations = comparison_operations


class NotExpression:
    def __init__(self, comparison_expression: ComparisonExpression, is_not=False):
        self.comparison_expression = comparison_expression
        # 是否有not操作
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
