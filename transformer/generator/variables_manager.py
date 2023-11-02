from copy import copy

from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class VariablesManager:
    def __init__(self):
        self.count_num = 99
        # 当前有效的用户定义的变量名
        self.user_variables = []
        # 当前有效的用户定义的对象节点名：对象节点
        self.user_object_nodes_dict = {}
        self.user_edges_dict = {}
        self.user_paths_dict = {}
        # 当前有效的在updating语句中定义的对象节点名：对象节点
        self.updating_object_nodes_dict = {}
        self.updating_edges_dict = {}
        self.expression_converter = None

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
        self.user_object_nodes_dict = {}
        self.user_edges_dict = {}
        self.user_paths_dict = {}
        self.updating_object_nodes_dict = {}
        self.updating_edges_dict = {}
        self.updating_paths_dict = {}

    def update_yield_clause_variables(self, yield_clause: YieldClause):
        for yield_item in yield_clause.yield_items:
            if yield_item.variable:
                self.user_variables.append(yield_item.variable)
            else:
                self.user_variables.append(yield_item.procedure_result)

    def update_with_clause_variables(self, with_clause: WithClause):
        self.clear()
        for projection_item in with_clause.projection_items:
            if projection_item.variable:
                self.user_variables.append(projection_item.variable)

    def update_return_clause_variables(self, return_clause: WithClause):
        self.clear()
        for projection_item in return_clause.projection_items:
            if projection_item.variable:
                self.user_variables.append(projection_item.variable)

    def update_unwind_clause_variable(self, unwind_clause: UnwindClause):
        self.user_variables.append(unwind_clause.variable)

    def update_match_variables(self, match_clause: MatchClause):
        for pattern in match_clause.patterns:
            self.update_pattern_variables(pattern)

    def update_create_variables(self, create_clause: CreateClause):
        for pattern in create_clause.patterns:
            self.update_pattern_variables(pattern, True)

    def update_pattern_variables(self, pattern: Pattern, is_creating=False):
        pattern = pattern.pattern
        if pattern.__class__ == SPath:
            self.update_path_variables(pattern, is_creating)
        elif pattern.__class__ == TemporalPathCall:
            self.user_variables.append(pattern.variable)
            self.user_paths_dict[pattern.variable] = pattern
            self.update_path_variables(pattern.path, is_creating)

    def update_path_variables(self, path: SPath, is_creating=False):
        if path.variable:
            self.user_variables.append(path.variable)
            self.user_paths_dict[path.variable] = path
        for object_node in path.nodes:
            if object_node.variable:
                if object_node.variable in self.user_object_nodes_dict.keys():
                    object_node_in_dict = self.user_object_nodes_dict[object_node.variable]
                    object_node_in_dict.properties.update(object_node.properties)
                    if is_creating and object_node.variable in self.updating_object_nodes_dict.keys():
                        updating_object_node_in_dict = self.updating_object_nodes_dict[object_node.variable]
                        updating_object_node_in_dict.properties.update(object_node.properties)
                else:
                    self.user_variables.append(object_node.variable)
                    self.user_object_nodes_dict[object_node.variable] = copy(object_node)
                    if is_creating:
                        self.updating_object_nodes_dict[object_node.variable] = copy(object_node)

        for edge in path.edges:
            if edge.variable:
                if edge.variable in self.user_edges_dict.keys():
                    edge_in_dict = self.user_edges_dict[edge.variable]
                    edge_in_dict.properties.update(edge.properties)
                    if is_creating and edge.variable in self.updating_edges_dict.keys():
                        updating_edge_in_dict = self.updating_edges_dict[edge.variable]
                        updating_edge_in_dict.properties.update(edge.properties)
                else:
                    self.user_variables.append(edge.variable)
                    self.user_edges_dict[edge.variable] = copy(edge)
                    if is_creating:
                        self.updating_paths_dict[edge.variable] = copy(edge)
