from typing import List


class ListLiteral:
    # 注意：该处expressions为List[Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, expressions: List):
        self.expressions = expressions

    def convert(self):
        list_string = ""
        for index, expression in enumerate(self.expressions):
            if index != 0:
                list_string = list_string + ', '
            list_string = list_string + expression.convert()
        list_string = '[' + list_string + ']'
        return list_string

    def get_at_t_expressions(self) -> List:
        at_t_expressions = []
        for expression in self.expressions:
            at_t_expressions.extend(expression.get_at_t_expressions())
        return at_t_expressions


class MapLiteral:
    # 注意：该处key_values为dict[str, Expression]类型，由于与Expression相互引用，故此处不写明类型。
    def __init__(self, keys_values: dict):
        self.keys_values = keys_values

    def convert(self):
        map_string = ""
        for index, (key, value) in enumerate(self.keys_values.items()):
            if index != 0:
                map_string = map_string + ', '
            map_string = map_string + key + ': ' + value.convert()
        map_string = '{' + map_string + '}'
        return map_string

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

    def convert(self):
        return '( ' + self.expression.convert() + ' )'

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

    def convert(self):
        function_invocation_string = ""
        if self.is_distinct:
            function_invocation_string = function_invocation_string + 'DISTINCT '
        for index, expression in self.expressions:
            if index != 0:
                function_invocation_string = function_invocation_string + ','
            function_invocation_string = function_invocation_string + expression.convert()
        function_invocation_string = self.function_name + '( ' + function_invocation_string + ' )'
        return function_invocation_string

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

    def convert(self):
        if self.atom.__class__ == str:
            return self.atom
        return self.atom.convert()

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

    def convert(self):
        properties_labels_string = self.atom.convert()
        for proprety in self.property_chains:
            properties_labels_string = properties_labels_string + '.' + proprety
        for label in self.labels:
            properties_labels_string = properties_labels_string + ':' + label
        return properties_labels_string

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

    def convert(self):
        list_index_string = ""
        if self.principal_expression.__class__ == PropertiesLabelsExpression:
            list_index_string = self.principal_expression.convert()
        elif self.principal_expression.__class__ == AtTExpression:
            list_index_string = self.principal_expression.convert()

        if self.index_expression:
            list_index_string = list_index_string + '[' + self.index_expression.convert() + ']'
        if self.is_positive is False:
            list_index_string = '-' + list_index_string
        return list_index_string

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

    def convert(self):
        power_string = ""
        for index, list_expression in enumerate(self.list_index_expressions):
            if index == 0:
                power_string = list_expression.convert()
            else:
                power_string = power_string + '^' + list_expression.convert() + ''
        return power_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for list_index_expression in self.list_index_expressions:
            at_t_expressions.extend(list_index_expression.get_at_t_expressions())
        return at_t_expressions


class MultiplyDivideExpression:
    def __init__(self, left_expression: PowerExpression, multiply_divide_operation: str = None,
                 right_expression: PowerExpression = None):
        if multiply_divide_operation not in ['*', '/']:
            raise ValueError("The multiply_divide_operation must be '*' or '/'.")
        self.left_expression = left_expression
        self.multiply_divide_operation = multiply_divide_operation
        self.right_expression = right_expression

    def convert(self):
        multiply_divide_string = self.left_expression.convert()
        if self.multiply_divide_operation and self.right_expression:
            right_string = self.right_expression.convert()
            multiply_divide_string = multiply_divide_string + ' ' + self.multiply_divide_operation + ' ' + right_string
        return multiply_divide_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = self.left_expression.get_at_t_expressions()
        if self.right_expression:
            at_t_expressions.extend(self.right_expression.get_at_t_expressions())
        return at_t_expressions


class AddSubtractExpression:
    def __init__(self, multiply_divide_expressions: List[MultiplyDivideExpression],
                 add_subtract_operations: List[str] = None):
        self.multiply_divide_expressions = multiply_divide_expressions
        if add_subtract_operations is None:
            add_subtract_operations = []
        if len(multiply_divide_expressions) != len(add_subtract_operations) + 1:
            raise ValueError(
                "The numbers of the multiply_divide_expressions and add_subtract_operations are not matched.")
        for add_subtract_operation in add_subtract_operations:
            if add_subtract_operation not in ['-', '+']:
                raise ValueError("The add_subtract_operation must be '+' or '-'.")
        self.add_subtract_operations = add_subtract_operations

    def convert(self):
        add_subtract_string = self.multiply_divide_expressions[0].convert()
        index = 0
        if index < len(self.multiply_divide_expressions):
            add_subtract_string = add_subtract_string + ' ' + self.add_subtract_operations[
                index] + ' '
            add_subtract_string = add_subtract_string + self.multiply_divide_expressions[index + 1].convert()
            index = index + 1
        return add_subtract_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for multiply_divide_expression in self.multiply_divide_expressions:
            at_t_expressions.extend(multiply_divide_expression.get_at_t_expressions())
        return at_t_expressions


class TimePredicateExpression:
    def __init__(self, time_operation: str, add_or_subtract_expression: AddSubtractExpression = None):
        if time_operation.lower() not in ['during', 'overlaps']:
            raise ValueError("The time operation must be 'during' or 'overlaps'.")
        self.time_operation = time_operation
        self.add_or_subtract_expression = add_or_subtract_expression

    def convert(self):
        pass

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.add_or_subtract_expression.get_at_t_expressions()


class StringPredicateExpression:
    def __init__(self, string_operation: str, add_or_subtract_expression: AddSubtractExpression = None):
        if string_operation.lower() not in ['starts with', 'ends with', 'contains']:
            raise ValueError("The string operation must in 'starts with', 'ends with' and 'contains'.")
        self.string_operation = string_operation
        self.add_or_subtract_expression = add_or_subtract_expression

    def convert(self):
        return self.string_operation + ' ' + self.add_or_subtract_expression.convert()

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.add_or_subtract_expression.get_at_t_expressions()


class ListPredicateExpression:
    def __init__(self, add_or_subtract_expression: AddSubtractExpression = None):
        self.add_or_subtract_expression = add_or_subtract_expression

    def convert(self):
        return 'IN ' + self.add_or_subtract_expression.convert()

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.add_or_subtract_expression.get_at_t_expressions()


class NullPredicateExpression:
    def __init__(self, is_null: bool = True):
        # is_null为True表示IS NULL操作，反之表示IS NOT NULL操作
        self.is_null = is_null

    def convert(self):
        if self.is_null:
            return 'IS NULL'
        return 'IS NOT NULL'


# 相当于StringListNullPredicateExpression
class SubjectExpression:
    def __init__(self, add_or_subtract_expression: AddSubtractExpression,
                 predicate_expression: TimePredicateExpression | StringPredicateExpression | ListPredicateExpression | NullPredicateExpression = None):
        self.add_or_subtract_expression = add_or_subtract_expression
        self.predicate_expression = predicate_expression

    def convert(self):
        subject_string = self.add_or_subtract_expression.convert()
        if self.predicate_expression:
            predicate_string = ""
            if self.predicate_expression.__class__ == TimePredicateExpression:
                predicate_string = self.predicate_expression.convert()
            elif self.predicate_expression.__class__ == StringPredicateExpression:
                predicate_string = self.predicate_expression.convert()
            elif self.predicate_expression.__class__ == ListPredicateExpression:
                predicate_string = self.predicate_expression.convert()
            return subject_string + ' ' + predicate_string
        return subject_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = self.add_or_subtract_expression.get_at_t_expressions()
        if self.predicate_expression.__class__ in [TimePredicateExpression, StringPredicateExpression,
                                                   ListPredicateExpression]:
            at_t_expressions.extend(self.predicate_expression.get_at_t_expressions())
        return at_t_expressions


class ComparisonExpression:
    def __init__(self, subject_expressions: List[SubjectExpression], comparison_operations: List[str] = None):
        self.subject_expressions = subject_expressions
        if comparison_operations is None:
            comparison_operations = []
        if len(subject_expressions) != len(comparison_operations) + 1:
            raise ValueError("The numbers of the subject_expressions and comparison_operations are not matched.")
        for comparison_operation in comparison_operations:
            if comparison_operation not in ['=', '<>', '<', '>', '<=', '>=']:
                raise ValueError("The comparison operation must be '=', '<>', '<', '>', '<=' or '>='.")
        self.comparison_operations = comparison_operations

    def convert(self):
        comparison_string = self.subject_expressions[0].convert()
        index = 0
        if index < len(self.comparison_operations):
            comparison_string = comparison_string + ' ' + self.comparison_operations[index] + ' '
            comparison_string = comparison_string + self.subject_expressions[index + 1].convert()
            index = index + 1
        return comparison_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for subject_expression in self.subject_expressions:
            at_t_expressions.extend(subject_expression.get_at_t_expressions())
        return at_t_expressions


class NotExpression:
    def __init__(self, comparison_expression: ComparisonExpression, is_not=False):
        self.comparison_expression = comparison_expression
        self.is_not = is_not

    def convert(self):
        comparison_string = self.comparison_expression.convert()
        if self.is_not:
            comparison_string = 'NOT ' + comparison_string
        return comparison_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.comparison_expression.get_at_t_expressions()


class AndExpression:
    def __init__(self, not_expressions: List[NotExpression]):
        self.not_expressions = not_expressions

    def convert(self):
        and_expression_string = ""
        for index, not_expression in enumerate(self.not_expressions):
            if index != 0:
                and_expression_string = and_expression_string + ' OR '
            and_expression_string = and_expression_string + not_expression.convert()
        return and_expression_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for not_expression in self.not_expressions:
            at_t_expressions.extend(not_expression.get_at_t_expressions())
        return at_t_expressions


class XorExpression:
    def __init__(self, and_expressions: List[AndExpression]):
        self.and_expressions = and_expressions

    def convert(self):
        xor_expression_string = ""
        for index, and_expression in enumerate(self.and_expressions):
            if index != 0:
                xor_expression_string = xor_expression_string + ' XOR '
            xor_expression_string = xor_expression_string + and_expression.convert()
        return xor_expression_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for and_expression in self.and_expressions:
            at_t_expressions.extend(and_expression.get_at_t_expressions())
        return at_t_expressions


class OrExpression:
    def __init__(self, xor_expressions: List[XorExpression]):
        self.xor_expressions = xor_expressions

    def convert(self):
        or_expression_string = ""
        for index, xor_expression in enumerate(self.xor_expressions):
            if index != 0:
                or_expression_string = or_expression_string + ' OR '
            or_expression_string = or_expression_string + xor_expression.convert()
        return or_expression_string

    def get_at_t_expressions(self) -> List[AtTExpression]:
        at_t_expressions = []
        for xor_expression in self.xor_expressions:
            at_t_expressions.extend(xor_expression.get_at_t_expressions())
        return at_t_expressions


class Expression:
    def __init__(self, or_expression):
        self.or_expression = or_expression

    def convert(self):
        return self.or_expression.convert()

    def get_at_t_expressions(self) -> List[AtTExpression]:
        return self.or_expression.get_at_t_expression()
