from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class VariablesManager:
    def __init__(self, s_cypher_clause: SCypherClause):
        self.count_num = 99
        # 当前有效的用户定义的变量名
        self.user_variables = []
        self.updating_variables = []
        self.update_s_cypher_clause_variables(s_cypher_clause)

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

    def update_s_cypher_clause_variables(self, s_cypher_clause: SCypherClause):
        query_clause = s_cypher_clause.query_clause
        if query_clause.__class__ == UnionQueryClause:
            for multi_query_clause in query_clause.multi_query_clauses:
                self.update_multi_query_clause_variables(multi_query_clause)
        elif query_clause.__class__ == CallClause and query_clause.yield_clause:
            self.update_yield_clause_variables(query_clause.yield_clause)

    def update_yield_clause_variables(self, yield_clause: YieldClause):
        for yield_item in yield_clause.yield_items:
            if yield_item.variable:
                self.user_variables.append(yield_item.variable)
            else:
                self.user_variables.append(yield_item.procedure_result)

    def update_multi_query_clause_variables(self, multi_query_clause: MultiQueryClause):
        for with_query_clause in multi_query_clause.with_query_clauses:
            self.update_with_query_clause_variables(with_query_clause)
        self.update_single_query_clause_variables(multi_query_clause.single_query_clause)

    def update_single_query_clause_variables(self, single_query_clause: SingleQueryClause):
        for reading_clause in single_query_clause.reading_clauses:
            self.update_reading_clause_variables(reading_clause)
        for updating_clause in single_query_clause.updating_clauses:
            self.update_updating_clause_variables(updating_clause)
        if single_query_clause.return_clause:
            self.update_return_clause_variables(single_query_clause.return_clause)

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

    def update_with_query_clause_variables(self, with_query_clause: WithQueryClause):
        for reading_clause in with_query_clause.reading_clauses:
            self.update_reading_clause_variables(reading_clause)
        for updating_clause in with_query_clause.updating_clauses:
            self.update_updating_clause_variables(updating_clause)
        self.update_with_clause_variables(with_query_clause.with_clause)

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

        for edge in path.edges:
            if edge.variable:
                if is_updating and edge.variable not in self.user_variables:
                    self.updating_variables.append(edge.variable)
                self.user_variables.append(edge.variable)
