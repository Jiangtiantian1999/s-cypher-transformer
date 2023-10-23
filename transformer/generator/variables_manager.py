from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class VariablesManager:
    def __init__(self):
        self.count_num = 99
        # 用户定义的变量名/别名：对象
        self.variables_dict = {}
        # 是否返回所有对象
        self.is_all = False
        self.expression_converter = None

    # 获取新的变量名
    def get_random_variable(self) -> str:
        self.count_num = self.count_num + 1
        while "var" + str(self.count_num) in self.variables_dict.keys():
            self.count_num = self.count_num + 1
        return "var" + str(self.count_num)

    # 获取所有可返回的变量（返回*时调用）
    def get_variables(self) -> str:
        result = ""
        for index, variable in enumerate(self.variables_dict.keys()):
            if index != 0:
                result = result + ", "
            result = result + variable
        return result

    def get_yield_clause_variables_dict(self, yield_clause: YieldClause) -> dict:
        variables_dict = {}
        if yield_clause:
            for yield_item in yield_clause.yield_items:
                if yield_item.variable:
                    variables_dict[yield_item.variable] = yield_item.procedure_result
                else:
                    variables_dict[yield_item.procedure_result] = None
            return variables_dict
        return variables_dict

    def get_with_clause_variables_dict(self, with_clause: WithClause) -> dict:
        variables_dict = {}
        for projection_item in with_clause.projection_items:
            if projection_item.variable:
                variables_dict[projection_item.variable] = projection_item.expression
            else:
                variables_dict[self.expression_converter.convert_expression(
                    projection_item.expression)] = projection_item.expression
        return variables_dict

    def get_return_clause_variables_dict(self, return_clause: ReturnClause) -> dict:
        variables_dict = {}
        if return_clause:
            for projection_item in return_clause.projection_items:
                if projection_item.variable:
                    variables_dict[projection_item.variable] = projection_item.expression
                else:
                    variables_dict[self.expression_converter.convert_expression(
                        projection_item.expression)] = projection_item.expression
        return variables_dict

    def get_updating_clause_variables_dict(self,
                                           updating_clause: CreateClause | DeleteClause | StaleClause | SetClause | MergeClause | RemoveClause) -> dict:
        variables_dict = {}
        if updating_clause.__class__ in [CreateClause, MergeClause]:
            for pattern in updating_clause.patterns:
                variables_dict.update(self.get_pattern_variables_dict(pattern))
        return variables_dict

    def get_reading_clause_variables_dict(self, reading_clause: ReadingClause) -> dict:
        reading_clause = reading_clause.reading_clause
        if reading_clause.__class__ == MatchClause:
            variables_dict = {}
            for pattern in reading_clause.patterns:
                variables_dict.update(self.get_pattern_variables_dict(pattern))
            return variables_dict
        elif reading_clause.__class__ == UnwindClause:
            return {reading_clause.variable: reading_clause}
        elif reading_clause.__class__ == CallClause and reading_clause.yield_clause:
            return self.get_yield_clause_variables_dict(reading_clause.yield_clause)
        return {}

    def get_pattern_variables_dict(self, pattern: Pattern) -> dict:
        pattern = pattern.pattern
        if pattern.__class__ == SPath:
            # SPath/ObjectNode/PropertyNode/ValueNode/SEdge
            return self.get_path_variables_dict(pattern)
        elif pattern.__class__ == TemporalPathCall:
            # TemporalPathCall
            variables_dict = {pattern.variable: pattern}
            # SPath/ObjectNode/PropertyNode/ValueNode/SEdge
            variables_dict.update(self.get_path_variables_dict(pattern.path))
            return variables_dict
        return {}

    def get_path_variables_dict(self, path: SPath) -> dict:
        variables_dict = {}
        if path.variable:
            # SPath
            variables_dict[path.variable] = path
        for node in path.nodes:
            # ObjectNode/PropertyNode/ValueNode
            variables_dict.update(self.get_object_node_variables_dict(node))
        for edge in path.edges:
            if edge.variable:
                # SEdge
                variables_dict[edge.variable] = edge
        return variables_dict

    def get_object_node_variables_dict(self, object_node: ObjectNode) -> dict:
        variables_dict = {}
        if object_node.variable:
            # ObjectNode
            variables_dict[object_node.variable] = object_node
        # for key, value in object_node.properties.items():
        #     if key.variable:
        #         # PropertyNode
        #         variables_dict[key.variable] = key
        #     if value.variable:
        #         # ValueNode
        #         variables_dict[value.variable] = value
        return variables_dict
