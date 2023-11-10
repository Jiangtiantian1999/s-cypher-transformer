from typing import List

from transformer.ir.s_expression import Atom, Expression, PropertyLookup, PropertyValueAtTElement
from transformer.ir.s_graph import SPath


class TemporalPathCall:
    def __init__(self, variable: str, function_name: str, path: SPath):
        # 返回的时态路径变量名
        self.variable = variable
        self.function_name = function_name
        if len(path.nodes) != 2:
            raise ValueError("The length of the temporal path are not matched.")
        self.path = path


class Pattern:

    def __init__(self, pattern: SPath | TemporalPathCall):
        self.pattern = pattern


class ProjectionItem:

    def __init__(self, expression: Expression, variable: str = None):
        # 表达式
        self.expression = expression
        # 别名
        self.variable = variable


class YieldItem:

    def __init__(self, procedure_result: str, variable: str = None):
        # 返回结果
        self.procedure_result = procedure_result
        # 别名
        self.variable = variable


class DeleteItem:
    def __init__(self, expression: Expression, property_value_at_t_element: PropertyValueAtTElement = None):
        self.expression = expression
        self.property_value_at_t_element = property_value_at_t_element


class StaleItem:
    def __init__(self, expression: Expression, property_name: str = None, is_value=False):
        self.expression = expression
        if property_name is None and is_value is True:
            raise ValueError("Can't delete the value node without property name.")
        self.property_name = property_name
        # 删除的是否为值节点
        self.is_value = is_value


class LabelSetting:
    def __init__(self, variable: str, labels: List[str]):
        self.variable = variable
        self.labels = labels


class RemovePropertyExpression:
    def __init__(self, atom: Atom, property_name: str, property_chains: List[PropertyLookup] = None):
        self.atom = atom
        self.property_name = property_name
        if property_chains is None:
            property_chains = []
        self.property_chains = property_chains


class IntervalSetting:

    def __init__(self, object_variable: str, interval: Expression,
                 property_value_at_t_element: PropertyValueAtTElement = None):
        self.object_variable = object_variable
        self.interval = interval
        self.property_value_at_t_element = property_value_at_t_element


class SetPropertyExpression:
    def __init__(self, atom: Atom, property_chains: List[PropertyLookup]):
        self.atom = atom
        if len(property_chains) == 0:
            raise ValueError("The property chains can't be empty.")
        self.property_chains = property_chains


class ExpressionSetting:
    def __init__(self, expression_left: SetPropertyExpression | str, expression_right: Expression, is_added: False):
        if expression_left.__class__ == SetPropertyExpression and is_added is True:
            raise ValueError("The property expression can't be added.")
        self.expression_left = expression_left
        self.expression_right = expression_right
        # 是否为+=，默认为=
        self.is_added = is_added
