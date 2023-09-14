from typing import List


class ListLiteral:
    # 注意：该处expressions为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, expressions: List):
        self.expressions = expressions

    def get_at_t_expressions(self) -> List:
        at_t_expressions = []
        for expression in self.expressions:
            at_t_expressions.extend(expression.get_at_t_expressions())
        return at_t_expressions


class MapLiteral:
    # 注意：该处key_values为dict[str, Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, keys_values: dict):
        self.keys_values = keys_values

    def get_at_t_expressions(self) -> List:
        at_t_expressions = []
        for expression in self.keys_values.values():
            at_t_expressions.extend(expression.get_at_t_expressions())
        return at_t_expressions


class CaseExpression:
    pass


class ListComprehension:
    pass


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

    def get_at_t_expressions(self) -> List:
        return self.expression.get_at_t_expressions()


class FunctionInvocation:
    # 注意：该处expressions为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, function_name: str, is_distinct=False, expressions: List = None):
        self.function_name = function_name
        self.is_distinct = is_distinct
        if expressions is None:
            expressions = []
        self.expressions = expressions

    def get_at_t_expressions(self) -> List:
        at_t_expressions = []
        for expression in self.expressions:
            at_t_expressions.extend(expression.get_at_t_expressions())
        return at_t_expressions


class ExistentialSubquery:
    pass


# 基础原子对象
class Atom:
    def __init__(self,
                 atom: str | ListLiteral | MapLiteral | CaseExpression | ListComprehension | PatternComprehension | Quantifier | PatternPredicate | ParenthesizedExpression | FunctionInvocation | ExistentialSubquery):
        # BooleanLiteral、NULL、NumberLiteral、StringLiteral、COUNT(*)和Parameter类型可以直接用str存储
        self.atom = atom

    def get_at_t_expressions(self) -> List:
        if self.atom.__class__ in [ListLiteral, MapLiteral, CaseExpression, ListComprehension, PatternComprehension,
                                   Quantifier, ParenthesizedExpression, FunctionInvocation]:
            return self.atom.get_at_t_expression()
        return []


class PropertiesLabelsExpression:
    def __init__(self, atom: Atom, property_chains: List[str] = None, labels: List[str] = None):
        self.atom = atom
        if property_chains is None:
            property_chains = []
        self.property_chains = property_chains
        if labels is None:
            labels = []
        self.labels = labels

    def get_at_t_expressions(self) -> List:
        return self.atom.get_at_t_expressions()


class AtTExpression:
    def __init__(self, atom: Atom, property_chains: List[str] = None, is_value: bool = False,
                 time_property_chains: List[str] = None):
        self.atom = atom
        if property_chains is None:
            property_chains = []
        self.property_chains = property_chains
        # 是否获取值节点的有效时间
        self.is_value = is_value
        # 获取有效时间的属性
        if time_property_chains is None:
            time_property_chains = []
        self.time_property_chains = time_property_chains


# 合并了oC_UnaryAddOrSubtractExpression和oC_ListOperatorExpression
class ListIndexExpression:
    # 注意：该处index_expression为Expression类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, principal_expression: PropertiesLabelsExpression | AtTExpression, is_positive=True,
                 index_expression=None):
        self.principal_expression = principal_expression
        # 是否为正
        self.is_positive = is_positive
        # 列表索引
        self.index_expression = index_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        if self.principal_expression.__class__ == PropertiesLabelsExpression:
            at_t_expressions = self.principal_expression.get_at_t_expressions()
        elif self.principal_expression.__class__ == AtTExpression:
            at_t_expressions = self.principal_expression
        at_t_expressions.extend(self.index_expression.get_at_t_expressions())
        return at_t_expressions


class PowerExpression:
    def __init__(self, list_index_expressions: List[ListIndexExpression]):
        self.list_index_expressions = list_index_expressions

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for list_index_expression in self.list_index_expressions:
            at_t_expressions.extend(list_index_expression.get_at_t_expressions())
        return at_t_expressions


class MultiplyDivideExpression:
    def __init__(self, left_expression: PowerExpression, multiply_divide_operation: str = None,
                 right_expression: PowerExpression = None):
        if multiply_divide_operation not in ['*', '/']:
            raise ValueError("The multiply_divide_operation must in '*' and '/'.")
        self.left_expression = left_expression
        self.multiply_divide_operation = multiply_divide_operation
        self.right_expression = right_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = self.left_expression.get_at_t_expressions()
        if self.right_expression:
            at_t_expressions.extend(self.right_expression.get_at_t_expressions())
        return at_t_expressions


class AddSubtractExpression:
    def __init__(self, left_expression: MultiplyDivideExpression, add_subtract_operation: str = None,
                 right_expression: MultiplyDivideExpression = None):
        if add_subtract_operation not in ['-', '+']:
            raise ValueError("The add_subtract_operation must in '-' and '+'.")
        self.left_expression = left_expression
        self.add_subtract_operation = add_subtract_operation
        self.right_expression = right_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = self.left_expression.get_at_t_expressions()
        if self.right_expression:
            at_t_expressions.extend(self.right_expression.get_at_t_expressions())
        return at_t_expressions


class TimePredicateExpression:
    def __init__(self, time_operation: str, add_or_subtract_expression: AddSubtractExpression = None):
        if time_operation.lower() not in ['during', 'overlaps']:
            raise ValueError("The time operation must in 'during' and 'overlaps'.")
        self.time_operation = time_operation
        self.add_or_subtract_expression = add_or_subtract_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.add_or_subtract_expression.get_at_t_expressions()


class StringPredicateExpression:
    def __init__(self, string_operation: str, add_or_subtract_expression: AddSubtractExpression = None):
        if string_operation.lower() not in ['starts with', 'ends with', 'contains']:
            raise ValueError("The string operation must in 'starts with', 'ends with' and 'contains'.")
        self.string_operation = string_operation
        self.add_or_subtract_expression = add_or_subtract_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.add_or_subtract_expression.get_at_t_expressions()


class ListPredicateExpression:
    def __init__(self, add_or_subtract_expression: AddSubtractExpression = None):
        self.add_or_subtract_expression = add_or_subtract_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.add_or_subtract_expression.get_at_t_expressions()


class NullPredicateExpression:
    def __init__(self, is_null: bool = True):
        # is_null为True表示IS NULL操作，反之表示IS NOT NULL操作
        self.is_null = is_null


# 相当于StringListNullPredicateExpression
class SubjectExpression:
    def __init__(self, add_or_subtract_expression: AddSubtractExpression,
                 predicate_expression: TimePredicateExpression | StringPredicateExpression | ListPredicateExpression | NullPredicateExpression = None):
        self.add_or_subtract_expression = add_or_subtract_expression
        self.predicate_expression = predicate_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = self.add_or_subtract_expression.get_at_t_expressions()
        if self.predicate_expression.__class__ in [TimePredicateExpression, StringPredicateExpression,
                                                   ListPredicateExpression]:
            at_t_expressions.extend(self.predicate_expression.get_at_t_expressions())
        return at_t_expressions


class ComparisonExpression:
    def __init__(self, left_expression: SubjectExpression, comparison_operation: str = None,
                 right_expression: SubjectExpression = None):
        if comparison_operation not in ['=', '<>', '<', '>', '<=', '>=']:
            raise ValueError("The comparison operation must in '=', '<>', '<', '>', '<=', '>='.")
        self.left_expression = left_expression
        self.comparison_operation = comparison_operation
        self.right_expression = right_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = self.left_expression.get_at_t_expressions()
        if self.right_expression:
            at_t_expressions.extend(self.right_expression.get_at_t_expressions())
        return at_t_expressions


class NotExpression:
    def __init__(self, comparison_expression: ComparisonExpression, is_not=False):
        self.comparison_expression = comparison_expression
        self.is_not = is_not

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.comparison_expression.get_at_t_expressions()


class AndExpression:
    def __init__(self, not_expressions: List[NotExpression]):
        self.not_expressions = not_expressions

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for not_expression in self.not_expressions:
            at_t_expressions.extend(not_expression.get_at_t_expressions())
        return at_t_expressions


class XorExpression:
    def __init__(self, and_expressions: List[AndExpression]):
        self.and_expressions = and_expressions

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for and_expression in self.and_expressions:
            at_t_expressions.extend(and_expression.get_at_t_expressions())
        return at_t_expressions


class OrExpression:
    def __init__(self, xor_expressions: List[XorExpression]):
        self.xor_expressions = xor_expressions

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for xor_expression in self.xor_expressions:
            at_t_expressions.extend(xor_expression.get_at_t_expressions())
        return at_t_expressions


class Expression:
    def __init__(self, or_expression):
        self.or_expression = or_expression

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.or_expression.get_at_t_expression()
