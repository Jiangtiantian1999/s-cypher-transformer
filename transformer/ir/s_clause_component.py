from typing import List

from transformer.ir.s_expression import Atom, Expression
from transformer.ir.s_graph import SPath, AtTElement


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
    def __init__(self, expression: Expression, property_name: str = None, is_value=False):
        self.expression = expression
        if property_name is None and is_value is True:
            raise ValueError("Can't delete the value node without property name.")
        self.property_name = property_name
        # 删除的是否为值节点
        self.is_value = is_value


class PropertyExpression:
    def __init__(self, atom: Atom, property_chains: List[str]):
        self.atom = atom
        self.property_chains = property_chains


class LabelSetting:
    def __init__(self, variable: str, labels: List[str]):
        self.variable = variable
        self.labels = labels


class RemoveItem:
    def __init__(self, item: LabelSetting | PropertyExpression):
        self.item = item


class IntervalSetting:

    def __init__(self, object_variable: str, object_interval: AtTElement = None, property_variable: str = None,
                 property_interval: AtTElement = None, value_expression: Expression = None,
                 value_interval: AtTElement = None):
        if property_variable is None and property_interval is not None:
            raise ValueError("The property name must be specified before specifying the effective time.")
        if object_interval is None and property_interval is None and value_expression is None and value_interval is None:
            raise ValueError("Either set the effective time or set the property value.")
        self.object_variable = object_variable
        self.object_interval = object_interval
        self.property_variable = property_variable
        self.property_interval = property_interval
        self.value_expression = value_expression
        self.value_interval = value_interval


class ExpressionSetting:
    def __init__(self, expression_left: PropertyExpression | str, expression_right: Expression, is_added: False):
        if expression_left.__class__ == PropertyExpression and is_added is True:
            raise ValueError("The property expression can't be added.")
        self.expression_left = expression_left
        self.expression_right = expression_right
        # 是否为+=，默认为=
        self.is_added = is_added
