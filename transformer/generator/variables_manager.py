from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class VariablesManager:
    count_num = 99
    # 原句里自带的变量名/别名->对应实体对象/原表达式
    variables_dict = {}
    # 当前可返回的变量名/别名->对应实体对象/原表达式
    return_variables_dict = {}

    def __init__(self, s_cypher_clause: SCypherClause):
        self.variables_dict = self.get_s_cypher_clause_variables_dict(s_cypher_clause)

    # 获取新的变量名
    def get_random_variable(self) -> str:
        self.count_num = self.count_num + 1
        while "var" + str(self.count_num) in self.variables_dict.keys():
            self.count_num = self.count_num + 1
        return "var" + str(self.count_num)

    # 获取所有可返回的变量（返回*时调用）
    def get_return_variables(self) -> str:
        result = ""
        for index, variable in enumerate(self.return_variables_dict.keys()):
            if index != 0:
                result = result + ", "
            result = result + variable
        return result

    def get_s_cypher_clause_variables_dict(self, s_cypher_clause: SCypherClause) -> dict:
        if s_cypher_clause.query_clause.__class__ == UnionQueryClause:
            return self.get_union_query_clause_variables_dict(s_cypher_clause.query_clause)
        elif s_cypher_clause.query_clause.__class__ == CallClause:
            return self.get_call_clause_variables_dict(s_cypher_clause.query_clause)
        return {}

    def get_union_query_clause_variables_dict(self, union_query_clause: UnionQueryClause) -> dict:
        variables_dict = {}
        for multi_query_clause in union_query_clause.multi_query_clauses:
            variables_dict.update(self.get_multi_query_clause_variables_dict(multi_query_clause))
        return variables_dict

    def get_call_clause_variables_dict(self, call_clause: CallClause) -> dict:
        variables_dict = {}
        if call_clause.yield_clause:
            for yield_item in call_clause.yield_clause.yield_items:
                if yield_item.variable:
                    variables_dict[yield_item.variable] = yield_item.procedure_result
                else:
                    variables_dict[yield_item.procedure_result] = call_clause
            return variables_dict
        return variables_dict

    def get_multi_query_clause_variables_dict(self, multi_query_clause: MultiQueryClause) -> dict:
        variables_dict = self.get_single_query_clause_variables_dict(multi_query_clause.single_query_clause)
        for with_query_clause in multi_query_clause.with_query_clauses:
            variables_dict.update(self.get_with_query_clause_variables_dict(with_query_clause))
        return variables_dict

    def get_with_query_clause_variables_dict(self, with_query_clause: WithQueryClause) -> dict:
        variables_dict = {}
        for projection_item in with_query_clause.with_clause.projection_items:
            if projection_item.variable:
                variables_dict[projection_item.variable] = projection_item.expression
        for reading_clause in with_query_clause.reading_clauses:
            variables_dict.update(self.get_reading_clause_variable_dict(reading_clause))
        for updating_clause in with_query_clause.updating_clauses:
            variables_dict.update(self.get_update_clause_variables_dict(updating_clause))
        return variables_dict

    def get_single_query_clause_variables_dict(self, single_query_clause: SingleQueryClause) -> dict:
        variables_dict = {}
        if single_query_clause.return_clause:
            for projection_item in single_query_clause.return_clause.projection_items:
                if projection_item.variable:
                    variables_dict[projection_item.variable] = projection_item.expression
        for reading_clause in single_query_clause.reading_clauses:
            variables_dict.update(self.get_reading_clause_variable_dict(reading_clause))
        for updating_clause in single_query_clause.updating_clauses:
            variables_dict.update(self.get_update_clause_variables_dict(updating_clause))
        return variables_dict

    def get_update_clause_variables_dict(self, update_clause: UpdatingClause) -> dict:
        update_clause = update_clause.update_clause
        variables_dict = {}
        if update_clause.__class__ in [CreateClause, MergeClause]:
            for pattern in update_clause.patterns:
                variables_dict.update(self.get_pattern_variables_dict(pattern))
        return variables_dict

    def get_reading_clause_variable_dict(self, reading_clause: ReadingClause) -> dict:
        reading_clause = reading_clause.reading_clause
        if reading_clause.__class__ == MatchClause:
            variables_dict = {}
            for pattern in reading_clause.patterns:
                variables_dict.update(self.get_pattern_variables_dict(pattern))
            return variables_dict
        elif reading_clause.__class__ == UnwindClause:
            return {reading_clause.variable: reading_clause}
        elif reading_clause.__class__ == CallClause:
            return self.get_call_clause_variables_dict(reading_clause)
        return {}

    def get_pattern_variables_dict(self, pattern: Pattern) -> dict:
        pattern = pattern.pattern
        if pattern.__class__ == SPath:
            return self.get_path_variables_dict(pattern)
        elif pattern.__class__ == TemporalPathCall:
            variables_dict = {pattern.variable: pattern}
            variables_dict.update(self.get_path_variables_dict(pattern.path))
            return variables_dict
        return {}

    def get_path_variables_dict(self, path: SPath) -> dict:
        variables_dict = {}
        if path.variable:
            variables_dict[path.variable] = path
        for node in path.nodes:
            variables_dict.update(self.get_object_node_variables_dict(node))
        for edge in path.edges:
            if edge.variable:
                variables_dict[edge.variable] = edge
        return variables_dict

    def get_object_node_variables_dict(self, object_node: ObjectNode) -> dict:
        variables_dict = {}
        if object_node.variable:
            variables_dict[object_node.variable] = object_node
        for key, value in object_node.properties.items():
            if key.variable:
                variables_dict[key.variable] = key
            if value.variable:
                variables_dict[value.variable] = value
        return variables_dict
