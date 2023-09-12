from typing import List

from transformer.ir.s_graph import *


class TemporalPathCall:
    def __init__(self, variable: str, function_name: str, path: SPath):
        # 时态路径变量名
        self.variable = variable
        self.function_name = function_name
        if len(path.nodes) != 2:
            raise ValueError("The length of the temporal path  are not matched.")
        self.path = path
        self.start_node = path.nodes[0]
        self.edge = path.edges[0]
        self.end_node = path.nodes[1]

    def get_variables_dict(self):
        variables_dict = {self.variable: self}
        variables_dict.update(self.start_node.get_variables_dict())
        variables_dict.update(self.edge.get_variables_dict())
        variables_dict.update(self.end_node.get_variables_dict())
        return variables_dict


class Pattern:

    def __init__(self, pattern: SPath | TemporalPathCall):
        self.pattern = pattern

    def get_variables_dict(self):
        self.pattern.get_variables_dict()


class ProjectionItem:

    def __init__(self, is_all: bool = False, expression: Exception = None, variable: str = None):
        # 要么为*，要么为expression( as variable)
        if is_all is False and expression is None:
            raise ValueError("The projection item can't be empty.")
        # 是否返回所有变量，即return *
        self.is_all = is_all
        # 表达式
        self.expression = expression
        # 别名
        self.variable = variable
