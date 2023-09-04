from __future__ import annotations

from transformer.ir.s_graph import SNode, SPath


class TemporalPathCall:
    def __init__(self, variable: str, function_name: str, path: SPath):
        self.variable = variable
        self.function_name = function_name
        self.path = path


class Pattern:

    def __init__(self, pattern: SPath | TemporalPathCall):
        if pattern.__class__ == SPath.__class__:
            # 单点或路径
            self.path = pattern
        else:
            # 查找时态路径
            self.temporal_path_call = pattern

    def get_variables(self):
        if self.path is not None:
            return self.path.get_variables()
        else:
            variables = [self.temporal_path_call.variable]
            variables.extend(self.temporal_path_call.path.get_variables())
            return variables


class Expression:
    def get_variables(self):
        return []


class ProjectionItem:
    def get_variables(self):
        return []
