from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class VariablesManager:
    def __init__(self):
        self.count_num = 99
        # 当前有效的用户定义的变量
        self.user_variables = []
        # 当前有效的用户定义的对象节点的变量名：对象节点对象
        self.user_object_nodes_dict = {}
        self.expression_converter = None

    # 获取新的变量名
    def get_random_variable(self) -> str:
        self.count_num = self.count_num + 1
        variable = "var" + str(self.count_num)
        while variable in self.user_variables:
            self.count_num = self.count_num + 1
            variable = "var" + str(self.count_num)
        return variable

    def clear_variables(self):
        self.user_variables = []
        self.user_object_nodes_dict = {}
        self.object_nodes_dict = {}

    def update_yield_clause_variables(self, yield_clause: YieldClause):
        for yield_item in yield_clause.yield_items:
            if yield_item.variable:
                if yield_item.variable not in self.user_variables:
                    self.user_variables.append(yield_item.variable)
            else:
                if yield_item.procedure_result not in self.user_variables:
                    self.user_variables.append(yield_item.procedure_result)

    def update_with_clause_variables(self, with_clause: WithClause):
        self.clear_variables()
        for projection_item in with_clause.projection_items:
            if projection_item.variable:
                self.user_variables.append(projection_item.variable)
            else:
                expression_string = self.expression_converter.convert_expression(projection_item.expression)
                if expression_string not in self.user_variables:
                    self.user_variables.append(expression_string)

    def update_updating_clause_variables(self,
                                         updating_clause: CreateClause | DeleteClause | StaleClause | SetClause | MergeClause | RemoveClause):
        if updating_clause.__class__ in [CreateClause, MergeClause]:
            for pattern in updating_clause.patterns:
                self.update_pattern_variables(pattern)

    def update_reading_clause_variables(self, reading_clause: ReadingClause):
        reading_clause = reading_clause.reading_clause
        if reading_clause.__class__ == MatchClause:
            for pattern in reading_clause.patterns:
                self.update_pattern_variables(pattern)
        elif reading_clause.__class__ == UnwindClause:
            if reading_clause.variable not in self.user_variables:
                self.user_variables.append(reading_clause.variable)
        elif reading_clause.__class__ == CallClause and reading_clause.yield_clause:
            self.update_yield_clause_variables(reading_clause.yield_clause)

    def update_pattern_variables(self, pattern: Pattern):
        pattern = pattern.pattern
        if pattern.__class__ == SPath:
            self.update_path_variables(pattern)
        elif pattern.__class__ == TemporalPathCall:
            if pattern.variable not in self.user_variables:
                self.user_variables.append(pattern.variable)
            self.update_path_variables(pattern.path)

    def update_path_variables(self, path: SPath):
        if path.variable and path.variable not in self.user_variables:
            self.user_variables.append(path.variable)
        for object_node in path.nodes:
            if object_node.variable and object_node.variable not in self.user_variables:
                self.user_object_nodes_dict[object_node.variable] = object_node
                self.user_variables.append(object_node.variable)
        for edge in path.edges:
            if edge.variable and edge.variable in self.user_variables:
                self.user_variables.append(edge.variable)
