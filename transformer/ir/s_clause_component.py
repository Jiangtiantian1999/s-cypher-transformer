from typing import List

from transformer.exceptions.s_exception import TranslateError
from transformer.ir.s_expression import Atom, Expression, PropertyLookup, AtTElement
from transformer.ir.s_graph import SPath


class TemporalPathCall:
    def __init__(self, variable: str, function_name: str, path: SPath):
        # 返回的时态路径变量名
        self.variable = variable
        self.function_name = function_name
        if len(path.nodes) != 2:
            raise TranslateError("The length of the temporal path are not matched.")
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
    def __init__(self, expression: Expression, property_name: str = None, time_window: bool | AtTElement = None):
        self.expression = expression
        self.property_name = property_name
        self.time_window = time_window


class StaleItem:
    def __init__(self, expression: Expression, property_name: str = None, is_value=False):
        self.expression = expression
        if property_name is None and is_value is True:
            raise TranslateError("Can't delete the value node without property name.")
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


class NodeIntervalSetting:
    def __init__(self, variable: str, effective_time: AtTElement = None):
        self.variable = variable
        self.effective_time = effective_time


class EffectiveTimeSetting:

    def __init__(self, object_setting: NodeIntervalSetting, property_setting: NodeIntervalSetting = None,
                 value_setting: NodeIntervalSetting = None):
        if property_setting is None and value_setting is not None:
            raise TranslateError("Can't specify value node before specifying property node.")
        self.object_setting = object_setting
        self.property_setting = property_setting
        self.value_setting = value_setting


class SetPropertyExpression:
    def __init__(self, atom: Atom, property_chains: List[PropertyLookup]):
        self.atom = atom
        if len(property_chains) == 0:
            raise TranslateError("The property chains can't be empty.")
        self.property_chains = property_chains


class ExpressionSetting:
    def __init__(self, expression_left: SetPropertyExpression | str, expression_right: Expression, is_added: False):
        if expression_left.__class__ == SetPropertyExpression and is_added is True:
            raise TranslateError("The property expression can't be added.")
        self.expression_left = expression_left
        self.expression_right = expression_right
        # 是否为+=，默认为=
        self.is_added = is_added
