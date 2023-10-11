from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.graph_converter import GraphConverter
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class ClauseConverter:
    variables_manager = None
    expression_converter = None
    graph_converter = None

    def __init__(self, variables_manager: VariablesManager):
        self.variables_manager = variables_manager
        self.expression_converter = ExpressionConverter()
        self.graph_converter = GraphConverter(self.variables_manager, self.expression_converter)

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
        for index, input_item in enumerate(call_clause.input_items):
            if index != 0:
                input_string = input_string + ", "
            input_string = input_string + self.expression_converter.convert_expression(input_item)
        if input_string != "":
            call_string = call_string + '(' + input_string + ')'
        if call_clause.yield_clause:
            call_string = call_string + '\n' + self.convert_yield_clause(call_clause.yield_clause)
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
            yield_clause_string = yield_clause_string + "\nWHERE " + self.expression_converter.convert_expression(
                yield_clause.where_expression)
        return yield_clause_string

    def convert_time_window_limit_clause(self, time_window_limit_clause: TimeWindowLimitClause) -> str:
        time_window_limit = time_window_limit_clause.time_window_limit
        if time_window_limit.__class__ == SnapshotClause:
            return "CALL scypher.snapshot(" + self.expression_converter.convert_expression(
                time_window_limit.time_point) + ')'
        elif time_window_limit.__class__ == ScopeClause:
            return "CALL scypher.scope(" + self.expression_converter.convert_expression(
                time_window_limit.interval) + ')'

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
            return "UNWIND " + self.expression_converter.convert_expression(
                reading_clause.expression) + " AS " + reading_clause.variable
        elif reading_clause.__class__ == CallClause:
            return self.convert_call_clause(reading_clause)

    def convert_match_clause(self, match_clause: MatchClause) -> str:
        match_string = "MATCH "
        if match_clause.is_optional:
            match_string = "OPTIONAL MATCH "
        call_string = ""
        interval_conditions = []
        for pattern in match_clause.patterns:
            pattern = pattern.pattern
            if pattern.__class__ == SPath:
                path_pattern, property_patterns, path_interval_conditions = self.graph_converter.convert_path(pattern,
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
                start_node_pattern, start_node_property_patterns, start_node_interval_conditions = self.graph_converter.convert_object_node(
                    pattern.path.nodes[0], match_clause.time_window)
                end_node_pattern, end_node_property_patterns, end_node_interval_conditions = self.graph_converter.convert_object_node(
                    pattern.path.nodes[1], match_clause.time_window)
                call_string = call_string + "MATCH " + start_node_pattern + ", " + end_node_pattern
                # 添加节点属性模式的匹配
                property_patterns, interval_conditions = start_node_property_patterns, start_node_interval_conditions
                property_patterns.extend(end_node_property_patterns)
                interval_conditions.extend(end_node_interval_conditions)
                for property_pattern in start_node_property_patterns:
                    call_string = call_string + ", " + property_pattern
                # 添加时态路径的时态条件限制
                if len(interval_conditions) != 0:
                    call_string = call_string + "\nWHERE "
                    for index, interval_condition in enumerate(interval_conditions):
                        if index != 0:
                            call_string = call_string + " and "
                        call_string = call_string + interval_condition
                # 限制路径的开始节点和结束节点
                if pattern.path.edges[0].direction == SEdge.LEFT:
                    parameters_string = pattern.path.nodes[1].variable + ", " + pattern.path.nodes[0].variable
                else:
                    parameters_string = pattern.path.nodes[0].variable + ", " + pattern.path.nodes[1].variable
                # 限制路径的标签
                if len(pattern.path.edges[0].labels) != 0:
                    parameters_string = parameters_string + ", " + str(pattern.path.edges[0].labels)
                else:
                    parameters_string = parameters_string + ", NULL"
                # 限制路径的长度
                if pattern.path.edges[0].length[0] is not None:
                    parameters_string = parameters_string + ", " + str(pattern.path.edges[0].length[0])
                else:
                    parameters_string = parameters_string + ", NULL"
                if pattern.path.edges[0].length[1] is not None:
                    parameters_string = parameters_string + ", " + str(pattern.path.edges[0].length[1])
                else:
                    parameters_string = parameters_string + ", NULL"
                # 限制路径的有效时间
                if pattern.path.edges[0].interval:
                    interval_from_string = self.graph_converter.convert_time_point_literval(
                        pattern.path.edges[0].interval.interval_from)
                    interval_to_string = self.graph_converter.convert_time_point_literval(
                        pattern.path.edges[0].interval.interval_to)
                    parameters_string = parameters_string + ", scypher.interval(" + interval_from_string + ", " + interval_to_string + ')'
                else:
                    parameters_string = parameters_string + ", NULL"
                # 限制路径的属性
                if len(pattern.path.edges[0].properties) != 0:
                    parameters_string = parameters_string + ", " + str(pattern.path.edges[0].properties)
                else:
                    parameters_string = parameters_string + ", NULL"
                call_string = call_string + "\nCALL scypher." + pattern.function_name + '(' + parameters_string + ')' + \
                              "\nYIELD " + pattern.variable
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
            raise ValueError("The where expression and the interval conditions can't be None at the same time.")
        where_string = "WHERE "
        if where_expression:
            expression_string = self.expression_converter.convert_expression(where_expression)
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
        if return_clause.is_distinct:
            return_string = "RETURN DISTINCT "
        for projection_item in return_clause.projection_items:
            if projection_item.is_all:
                # 返回所有用户指定的可返回的变量
                for variable in self.variables_manager.return_variables_dict.keys():
                    if return_string not in ["RETURN ", "RETURN DISTINCT "]:
                        return_string = return_string + ", "
                    return_string = return_string + variable
            elif projection_item.expression:
                if return_string not in ["RETURN ", "RETURN DISTINCT "]:
                    return_string = return_string + ", "
                return_string = return_string + self.expression_converter.convert_expression(projection_item.expression)
                if projection_item.variable:
                    return_string = return_string + " AS " + projection_item.variable
        if return_clause.order_by_clause:
            return_string = return_string + '\n' + self.convert_order_by_clause(return_clause.order_by_clause)
        if return_clause.skip_expression:
            return_string = return_string + "\nSKIP " + self.expression_converter.convert_expression(
                return_clause.skip_expression)
        if return_clause.limit_expression:
            return_string = return_string + "\nSKIP " + self.expression_converter.convert_expression(
                return_clause.limit_expression)
        return return_string

    def convert_order_by_clause(self, order_by_clause: OrderByClause) -> str:
        order_by_clause_string = ""
        for index, (key, value) in enumerate(order_by_clause.sort_items.items()):
            if index != 0:
                order_by_clause_string = order_by_clause_string + '\n'
            order_by_clause_string = order_by_clause_string + self.expression_converter.convert_expression(key)
            if value:
                order_by_clause_string = order_by_clause_string + ' ' + value
        return order_by_clause_string
