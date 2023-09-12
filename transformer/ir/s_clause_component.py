from typing import List

from transformer.ir.s_graph import SNode, SPath


class TemporalPathCall:
    def __init__(self, variable: str, function_name: str, path: SPath):
        self.variable = variable
        self.function_name = function_name
        if len(path.nodes) != 2:
            raise ValueError("The length of the temporal path  are not matched.")
        self.start_node = SPath
        self.path = path


class Pattern:

    def __init__(self, pattern: SPath | TemporalPathCall):
        if pattern.__class__ == SPath:
            # 单点或路径
            self.path = pattern
        else:
            # 查找时态路径
            self.temporal_path_call = pattern

    def get_variables_dict(self):
        if self.path is not None:
            return self.path.get_variables_dict()
        else:
            variables_dict = {self.temporal_path_call.variable: self.temporal_path_call}
            variables_dict.update(self.temporal_path_call.path.get_variables_dict())
            return variables_dict


class ProjectionItem:
    ALL_ITEM = '*'
    pass
