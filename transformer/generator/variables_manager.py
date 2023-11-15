from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class VariablesManager:
    def __init__(self):
        self.count_num = 99
        # 当前有效的用户定义的变量名
        self.user_variables = []
        self.updating_variables = []
        # union连接的各个语句的返回变量
        self.union_variables = []

    # 获取新的变量名
    def get_random_variable(self) -> str:
        self.count_num = self.count_num + 1
        variable = "var" + str(self.count_num)
        while variable in self.user_variables:
            self.count_num = self.count_num + 1
            variable = "var" + str(self.count_num)
        return variable

    def clear(self):
        self.user_variables = []
        self.updating_variables = []

    def update_multi_query_clause_variables(self):
        self.union_variables.append(self.user_variables)
        self.clear()

    def update_yield_clause_variables(self, yield_clause: YieldClause):
        for yield_item in yield_clause.yield_items:
            if yield_item.variable:
                self.user_variables.append(yield_item.variable)
            else:
                self.user_variables.append(yield_item.procedure_result)

    def update_reading_clause_variables(self, reading_clause: ReadingClause):
        if reading_clause.reading_clause.__class__ == MatchClause:
            for pattern in reading_clause.reading_clause.patterns:
                self.update_pattern_variables(pattern)
        elif reading_clause.reading_clause.__class__ == UnwindClause:
            self.user_variables.append(reading_clause.reading_clause.variable)
        elif reading_clause.reading_clause.__class__ == CallClause and reading_clause.reading_clause.yield_clause:
            self.update_yield_clause_variables(reading_clause.reading_clause.yield_clause)

    def update_updating_clause_variables(self, updating_clause: UpdatingClause):
        if updating_clause.updating_clause.__class__ == CreateClause:
            for pattern in updating_clause.updating_clause.patterns:
                self.update_pattern_variables(pattern, True)
        elif updating_clause.updating_clause.__class__ == MergeClause:
            self.update_pattern_variables(updating_clause.updating_clause.pattern, True)

    def update_with_clause_variables(self, with_clause: WithClause):
        if with_clause.is_all is None:
            self.clear()
        for projection_item in with_clause.projection_items:
            if projection_item.variable:
                self.user_variables.append(projection_item.variable)

    def update_return_clause_variables(self, return_clause: ReturnClause):
        self.clear()
        for projection_item in return_clause.projection_items:
            if projection_item.variable:
                self.user_variables.append(projection_item.variable)

    def update_pattern_variables(self, pattern: Pattern, is_updating=False):
        pattern = pattern.pattern
        if pattern.__class__ == SPath:
            self.update_path_variables(pattern, is_updating)
        elif pattern.__class__ == TemporalPathCall:
            self.user_variables.append(pattern.variable)

    def update_path_variables(self, path: SPath, is_updating=False):
        if path.variable:
            self.user_variables.append(path.variable)
        for object_node in path.nodes:
            if object_node.variable:
                if is_updating and object_node.variable not in self.user_variables:
                    self.updating_variables.append(object_node.variable)
                self.user_variables.append(object_node.variable)

        for edge in path.relationships:
            if edge.variable:
                if is_updating and edge.variable not in self.user_variables:
                    self.updating_variables.append(edge.variable)
                self.user_variables.append(edge.variable)
