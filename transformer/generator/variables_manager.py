from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class VariablesManager:
    def __init__(self):
        self.count_num = 99
        # 当前有效的用户定义的变量名：对象/类型
        self.user_variables_dict = {}
        self.expression_converter = None

    # 获取新的变量名
    def get_random_variable(self) -> str:
        self.count_num = self.count_num + 1
        variable = "var" + str(self.count_num)
        while variable in self.user_variables_dict.keys():
            self.count_num = self.count_num + 1
            variable = "var" + str(self.count_num)
        return variable

    def update_variable_dict(self, variable_dict: dict):
        self.user_variables_dict.update(variable_dict)

    def clear_variables_dict(self):
        self.user_variables_dict = {}

    def update_yield_clause_variables_dict(self, yield_clause: YieldClause):
        for yield_item in yield_clause.yield_items:
            if yield_item.variable:
                self.user_variables_dict.update({yield_item.variable: None})
            else:
                self.user_variables_dict.update({yield_item.procedure_result: None})

    def update_with_clause_variables_dict(self, with_clause: WithClause):
        self.clear_variables_dict()
        for projection_item in with_clause.projection_items:
            if projection_item.variable:
                self.user_variables_dict[projection_item.variable] = projection_item.expression.data_type

    def update_return_clause_variables_dict(self, return_clause: WithClause):
        self.clear_variables_dict()
        for projection_item in return_clause.projection_items:
            if projection_item.variable:
                self.user_variables_dict[projection_item.variable] = projection_item.expression.data_type

    def update_unwind_clause_variable_dict(self, unwind_clause: UnwindClause):
        if unwind_clause.expression.data_type.__class__ == list:
            self.user_variables_dict[unwind_clause.variable] = unwind_clause.expression.data_type[0]
        else:
            self.user_variables_dict[unwind_clause.variable] = None

    def update_match_variables_dict(self, match_clause: MatchClause):
        for pattern in match_clause.patterns:
            self.update_pattern_variables_dict(pattern)

    def update_create_variables_dict(self, create_clause: CreateClause):
        for pattern in create_clause.patterns:
            self.update_pattern_variables_dict(pattern)

    def update_pattern_variables_dict(self, pattern: Pattern):
        pattern = pattern.pattern
        if pattern.__class__ == SPath:
            self.user_variables_dict[pattern.variable] = pattern
            self.update_path_variables_dict(pattern)
        elif pattern.__class__ == TemporalPathCall:
            self.user_variables_dict[pattern.variable] = pattern
            self.update_path_variables_dict(pattern.path)

    def update_path_variables_dict(self, path: SPath):
        if path.variable:
            self.user_variables_dict[path.variable] = path
        for object_node in path.nodes:
            if object_node.variable:
                self.user_variables_dict[object_node.variable] = object_node
        for edge in path.edges:
            if edge.variable:
                self.user_variables_dict[edge.variable] = edge
