from transformer.ir.s_cypher_clause import *
from transformer.ir.s_expression import *
from transformer.ir.s_graph import *


class CypherGenerator:
    count_num = 99
    # 原句里自带的变量名
    variables_dict = []
    s_cypher_clause = None

    # 获取新的变量名
    def get_random_variable(self) -> str:
        self.count_num = self.count_num + 1
        while "var" + str(self.count_num) in self.variables_dict.keys():
            self.count_num = self.count_num + 1
        return "var" + str(self.count_num)

    def get_effective_variables(self) -> str:
        result = ""
        for index, variable in enumerate(self.variables_dict.keys()):
            if index != 0:
                result = result + ", "
            result = result + variable
        return result

    def generate_cypher_query(self, s_cypher_clause: SCypherClause) -> str:
        self.count_num = 99
        self.variables_dict = s_cypher_clause.get_variables_dict()
        self.s_cypher_clause = s_cypher_clause
        if s_cypher_clause.query_clause.__class__ == UnionQueryClause:
            return self.convert_union_query_clause(s_cypher_clause.query_clause)
        elif s_cypher_clause.query_clause.__class__ == CallClause:
            return self.convert_call_clause(s_cypher_clause.query_clause)
        elif s_cypher_clause.query_clause.__class__ == TimeWindowLimitClause:
            return s_cypher_clause.query_clause.convert()

    def convert_union_query_clause(self, union_query_clause: UnionQueryClause) -> str:
        union_query_string = self.convert_multi_query_clause(union_query_clause.multi_query_clauses[0])
        index = 1
        while index < len(union_query_clause.multi_query_clauses):
            operator = " UNION "
            if union_query_clause.is_all[index - 1]:
                operator = " UNION ALL "
            union_query_string = union_query_string + '\n' + operator + self.convert_multi_query_clause(
                union_query_clause.multi_query_clauses[index])
            index = index + 1
        return union_query_string

    def convert_call_clause(self, call_clause: CallClause) -> str:
        call_string = "CALL " + call_clause.procedure_name
        input_string = ""
        for input_item in call_clause.input_items:
            input_string = input_string + input_item.convert()
        if input_string != "":
            call_string = call_string + '(' + input_string + ')'
        if call_clause.yield_clause:
            call_string = call_string + self.convert_yield_clause(call_clause.yield_clause)
        return call_string

    def convert_yield_clause(self, yield_clause: YieldClause) -> str:
        yield_clause_string = "YIELD "
        for yield_item in yield_clause.yield_items:
            if yield_clause_string != "YIELD ":
                yield_clause_string = yield_clause_string + ", "
            yield_clause_string = yield_clause_string + yield_item.procedure_result
            if yield_item.variable:
                yield_clause_string = yield_clause_string + " AS " + yield_item.variable
        if yield_clause.where_expression:
            yield_clause_string = yield_clause_string + "\nWHERE " + yield_clause.where_expression.convert()
        return yield_clause_string

    def convert_multi_query_clause(self, multi_query_clause: MultiQueryClause) -> str:
        multi_query_string = ""
        # with连接的查询部分
        for with_query_clause in multi_query_clause.with_query_clauses:
            if multi_query_string != "":
                multi_query_string = multi_query_string + '\n'
            multi_query_string = multi_query_string + self.convert_with_query_clause(with_query_clause)
        # 最后一个查询部分
        if multi_query_string != "":
            multi_query_string = multi_query_string + '\n'
        multi_query_string = multi_query_string + self.convert_single_query_clause(
            multi_query_clause.single_query_clause)
        return multi_query_string

    def convert_with_query_clause(self, with_query_clause: WithQueryClause) -> str:
        with_query_string = ""
        # reading_clauses部分
        for reading_clause in with_query_clause.reading_clauses:
            if with_query_string == "":
                with_query_string = with_query_string + '\n'
            with_query_string = with_query_string + self.convert_reading_clause(reading_clause)
        # updating_clauses部分
        for updating_clause in with_query_clause.updating_clauses:
            if with_query_string == "":
                with_query_string = with_query_string + '\n'
            with_query_string = with_query_string + self.convert_updating_clause(updating_clause)
        # with_clause部分
        if with_query_string == "":
            with_query_string = with_query_string + '\n'
        with_query_string = with_query_string + with_query_clause.with_clause.convert()
        return with_query_string

    def convert_single_query_clause(self, single_query_clause: SingleQueryClause) -> str:
        single_query_string = ""
        # reading_clauses部分
        for reading_clause in single_query_clause.reading_clauses:
            if single_query_string != "":
                single_query_string = single_query_string + '\n'
            single_query_string = single_query_string + self.convert_reading_clause(reading_clause)
        # updating_clauses部分
        for updating_clause in single_query_clause.updating_clauses:
            if single_query_string != "":
                single_query_string = single_query_string + '\n'
            single_query_string = single_query_string + self.convert_updating_clause(updating_clause)
        # return_clause部分
        if single_query_clause.return_clause:
            if single_query_string != "":
                single_query_string = single_query_string + '\n'
            single_query_string = single_query_string + self.convert_return_clause(single_query_clause.return_clause)
        return single_query_string

    def convert_reading_clause(self, reading_clause: ReadingClause) -> str:
        reading_clause = reading_clause.reading_clause
        if reading_clause.__class__ == MatchClause:
            return self.convert_match_clause(reading_clause)
        elif reading_clause.__class__ == UnwindClause:
            return "UNWIND " + reading_clause.expression.convert() + " AS " + reading_clause.variable
        elif reading_clause.__class__ == CallClause:
            return self.convert_call_clause(reading_clause)

    def convert_match_clause(self, match_clause: MatchClause) -> str:
        call_string = ""
        match_string = "MATCH "
        if match_clause.is_optional:
            match_string = "OPTIONAL MATCH "
        interval_conditions = []
        for pattern in match_clause.patterns:
            pattern = pattern.pattern
            if pattern.__class__ == SPath:
                path_pattern, property_patterns, path_interval_conditions = self.convert_path(pattern,
                                                                                              match_clause.time_window)
                if match_string not in ["MATCH ", "OPTIONAL MATCH "]:
                    match_string = match_string + ", "
                match_string = match_string + path_pattern
                # 添加节点属性模式的匹配
                for property_pattern in property_patterns:
                    match_string = match_string + ", " + property_pattern
                interval_conditions.extend(path_interval_conditions)
            elif pattern.__class__ == TemporalPathCall:
                if call_string != "":
                    call_string = call_string + '\n'
                pattern.path.variable = self.get_random_variable()
                path_pattern, property_patterns, path_interval_conditions = self.convert_path(
                    pattern.path, match_clause.time_window)
                call_string = call_string + "MATCH " + path_pattern
                # 添加节点属性模式的匹配
                for property_pattern in property_patterns:
                    call_string = call_string + ", " + property_pattern
                # 添加时态路径的时态条件限制
                if len(path_interval_conditions) != 0:
                    call_string = call_string + "\nWHERE "
                    for index, interval_condition in enumerate(path_interval_conditions):
                        if index != 0:
                            call_string = call_string + " and "
                        call_string = call_string + interval_condition
                call_string = call_string + "\nCALL " + pattern.function_name + '(' + pattern.path.variable + ')' + \
                              "\nYIELD " + self.get_effective_variables()
        if match_string not in ["MATCH ", "OPTIONAL MATCH "]:
            if call_string != "":
                match_string = call_string + '\n' + match_string
            if match_clause.where_expression or len(interval_conditions) != 0:
                where_string = self.convert_where_clause(match_clause.where_expression, interval_conditions)
                match_string = match_string + '\n' + where_string
            return match_string
        else:
            return call_string

    def convert_where_clause(self, where_expression: Expression = None, interval_conditions: List[str] = None) -> str:
        if where_expression is None and (interval_conditions is None or len(interval_conditions) == 0):
            raise ValueError("The where_expression and the interval_conditions can't be None at the same time.")
        where_string = "WHERE "
        if where_expression:
            expression_string = where_expression.convert()
            where_string = where_string + expression_string
        if interval_conditions:
            for interval_condition in interval_conditions:
                if where_string != "WHERE ":
                    where_string = where_string + " and "
                where_string = where_string + interval_condition
        return where_string

    def convert_updating_clause(self, updating_clause: UpdatingClause) -> str:
        pass

    def convert_return_clause(self, return_clause: ReturnClause) -> str:
        return_string = "RETURN "
        for projection_item in return_clause.projection_items:
            if projection_item.is_all:
                for variable in self.variables_dict.keys():
                    if return_string != "RETURN ":
                        return_string = return_string + ", "
                    return_string = return_string + variable
            elif projection_item.expression:
                if return_string != "RETURN ":
                    return_string = return_string + ", "
                return_string = return_string + projection_item.expression.convert()
                if projection_item.variable:
                    return_string = return_string + " AS " + projection_item.variable
        return return_string

    def convert_object_node(self, object_node: ObjectNode, time_window: Expression = None) -> (
            str, List[str], List[str]):
        # 对象节点模式, 对象节点的有效时间限制
        object_pattern, object_interval_condition = self.convert_node(object_node, time_window)
        interval_conditions = [object_interval_condition]

        # 对象节点属性模式
        property_patterns = []
        for key, value in object_node.properties.items():
            property_pattern, property_interval_condition = self.convert_node(key)
            value_pattern, value_interval_condition = self.convert_node(value)
            property_patterns.append(
                object_pattern + "-[:OBJECT_PROPERTY]->" + property_pattern + "-[:PROPERTY_VALUE]->" + value_pattern)
            # 属性节点的有效时间限制
            interval_conditions.append(property_interval_condition)
            # 值节点的有效时间限制
            interval_conditions.append(value_interval_condition)

        return object_pattern, property_patterns, interval_conditions

    def convert_node(self, node: SNode, time_window: Expression = None) -> (str, List[str]):
        if node.variable is None:
            node.variable = self.get_random_variable()
        node_pattern = ""
        if node.variable:
            node_pattern = node.variable
        for label in node.labels:
            node_pattern = node_pattern + ':' + label
        if node.__class__ == PropertyNode:
            node_pattern = node_pattern + "{content: \"" + node.content + "\"}"
        elif node.__class__ == ValueNode:
            node_pattern = node_pattern + "{content: " + node.content.convert() + "}"
        node_pattern = '(' + node_pattern + ')'

        # 节点的有效时间限制
        if node.interval is None and time_window is None:
            interval_condition = "scypher.limitInterval(" + node.variable + ")"
        elif node.interval is not None and time_window is None:
            interval_condition = "scypher.limitInterval(" + node.variable + ", scypher.interval(" + \
                                 node.interval.interval_from.convert() + "," + node.interval.interval_to.convert() + "))"
        elif node.interval is None and time_window is not None:
            interval_condition = "scypher.limitInterval(" + node.variable + ", null, " + time_window.convert() + ")"
        else:
            interval_condition = "scypher.limitInterval(" + node.variable + ", scypher.interval(" + \
                                 node.interval.interval_from.convert() + "," + node.interval.interval_to.convert() + "), " + time_window.convert() + ")"

        return node_pattern, interval_condition

    def convert_edge(self, edge: SEdge, time_window: Expression = None) -> (str, List[str]):
        if edge.variable is None:
            edge.variable = self.get_random_variable()
        # 边模式
        edge_pattern = ""
        if edge.variable:
            edge_pattern = edge.variable
        for label in edge.labels:
            edge_pattern = edge_pattern + ':' + label
        if edge.length[0] != 1 or edge.length[1] != 1:
            if edge.length[0] == edge.length[1]:
                edge_pattern = edge_pattern + '*' + str(edge.length[0])
            else:
                edge_pattern = edge_pattern + '*' + str(edge.length[0]) + ".." + str(edge.length[1])
        if len(edge.properties) != 0:
            edge_pattern = edge_pattern + '{'
            for index, (key, value) in enumerate(edge.properties.items()):
                if index != 0:
                    edge_pattern = edge_pattern + ", "
                edge_pattern = edge_pattern + key + " : " + str(value)
            edge_pattern = edge_pattern + '}'
        if edge.variable or edge.labels or edge.length[0] != 1 or edge.length[1] != 1 or edge.properties:
            edge_pattern = "-[" + edge_pattern + "]-"
        else:
            edge_pattern = '-' + edge_pattern + '-'
        if edge.direction == edge.LEFT:
            edge_pattern = '<' + edge_pattern
        elif edge.direction == edge.RIGHT:
            edge_pattern = edge_pattern + '>'

        # 边的有效时间限制
        if edge.interval is None and time_window is None:
            interval_condition = "scypher.limitInterval(" + edge.variable + ')'
        elif edge.interval is not None and time_window is None:
            interval_condition = "scypher.limitInterval(" + edge.variable + ", scypher.interval(" + \
                                 edge.interval.interval_from.convert() + "," + edge.interval.interval_to.convert() + "))"
        elif edge.interval is None and time_window is not None:
            interval_condition = "scypher.limitInterval(" + edge.variable + ", null, " + time_window.convert() + ')'
        else:
            interval_condition = "scypher.limitInterval(" + edge.variable + ", scypher.interval(" + \
                                 edge.interval.interval_from.convert() + ',' + edge.interval.interval_to.convert() + "), " + time_window.convert() + ')'

        return edge_pattern, interval_condition

    def convert_path(self, path: SPath, time_window: Expression = None) -> (str, List[str], List[str]):
        # 路径模式，属性节点和值节点的模式，路径有效时间限制
        path_pattern, property_patterns, interval_conditions = self.convert_object_node(path.nodes[0], time_window)
        index = 1
        while index < len(path.nodes):
            # 生成边模式
            edge_pattern, edge_interval_condition = self.convert_edge(path.edges[index - 1], time_window)
            path_pattern = path_pattern + edge_pattern
            interval_conditions.append(edge_interval_condition)
            # 生成节点模式
            node_pattern, node_property_patterns, node_interval_conditions = self.convert_object_node(path.nodes[index],
                                                                                                      time_window)
            path_pattern = path_pattern + node_pattern
            property_patterns.extend(node_property_patterns)
            interval_conditions.extend(node_interval_conditions)

            index = index + 1
        if path.variable:
            path_pattern = path.variable + " = " + path_pattern
        return path_pattern, property_patterns, interval_conditions
