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

    def __init__(self, expression: Expression = None, variable: str = None):
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


class SetItem:
    def __init__(self, operator: str, object: str | Atom, labels: List[str] = None, object_interval: AtTElement = None,
                 property_variable: str = None, property_interval: AtTElement = None, value_interval: AtTElement = None,
                 value_expression: Expression = None):

        if operator == '=':
            if value_expression is None or labels:
                raise ValueError("The combination of the set item is incorrect.")
        elif operator == "+=":
            if value_expression is None or labels or object_interval or property_variable or property_interval or value_interval:
                raise ValueError("The combination of the set item is incorrect.")
        elif operator == "@T":
            if value_expression or labels or (property_variable is None and property_interval):
                raise ValueError("The combination of the set item is incorrect.")
        elif operator == ':':
            if labels is None or value_expression or object_interval or property_variable or property_interval or value_interval:
                raise ValueError("The combination of the set item is incorrect.")
        else:
            raise ValueError("Unknown set operation.")
        self.operator = operator
        # object为对象节点变量名或者Atom表达式
        self.object = object
        if labels:
            labels = []
        # 设置对象节点的label
        self.labels = labels
        # 设置对象节点的有效时间
        self.object_interval = object_interval
        # 为属性节点名称，或者( SP? oC_PropertyLookup )+的字符串表示
        self.property_variable = property_variable
        # 设置属性节点的有效时间
        self.property_interval = property_interval
        # 设置值节点的有效时间
        self.value_interval = value_interval
        # 设置值节点的值，或者表达式赋值
        self.value_expression = value_expression
