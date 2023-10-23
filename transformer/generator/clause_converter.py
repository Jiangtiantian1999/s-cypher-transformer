from transformer.conf.config_reader import ConfigReader
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class ClauseConverter:
    def __init__(self):
        self.variables_manager = None
        self.expression_converter = None
        self.graph_converter = None
        self.unwind_variables_dict = {}
        self.is_with_or_return = False

    def convert_s_cypher_clause(self, s_cypher_clause: SCypherClause) -> str:
        query_clause = s_cypher_clause.query_clause
        if query_clause.__class__ == UnionQueryClause:
            return self.convert_union_query_clause(query_clause)
        elif query_clause.__class__ == CallClause:
            return self.convert_call_clause(query_clause)
        elif query_clause.__class__ == TimeWindowLimitClause:
            return self.convert_time_window_limit_clause(query_clause)

    def convert_union_query_clause(self, union_query_clause: UnionQueryClause) -> str:
        union_query_clause_string = self.convert_multi_query_clause(union_query_clause.multi_query_clauses[0])

        for index, is_all in enumerate(union_query_clause.is_all):
            if is_all:
                operator = " UNION ALL "
            else:
                operator = " UNION "
            union_query_clause_string = union_query_clause_string + '\n' + operator + self.convert_multi_query_clause(
                union_query_clause.multi_query_clauses[index + 1])
        return union_query_clause_string

    def convert_call_clause(self, call_clause: CallClause) -> str:
        if call_clause.procedure_name in ConfigReader.config["SCYPHER"]["PROCEDURE_NAME"]:
            call_clause_string = "CALL scypher." + call_clause.procedure_name
        else:
            call_clause_string = "CALL " + call_clause.procedure_name
        input_string = ""
        for index, input_item in enumerate(call_clause.input_items):
            if index != 0:
                input_string = input_string + ", "
            input_string = input_string + self.expression_converter.convert_expression(input_item)
        call_clause_string = call_clause_string + '(' + input_string + ')'
        if call_clause.yield_clause:
            call_clause_string = call_clause_string + '\n' + self.convert_yield_clause(call_clause.yield_clause)
        return call_clause_string

    def convert_yield_clause(self, yield_clause: YieldClause) -> str:
        # 更新可返回的变量名/别名
        self.variables_manager.variables_dict.update(
            self.variables_manager.get_yield_clause_variables_dict(yield_clause))
        yield_clause_string = "YIELD "
        if yield_clause.is_all:
            yield_clause_string = "YIELD *, "
        for index, yield_item in enumerate(yield_clause.yield_items):
            if index != 0:
                yield_clause_string = yield_clause_string + ", "
            yield_clause_string = yield_clause_string + yield_item.procedure_result
            if yield_item.variable:
                yield_clause_string = yield_clause_string + " as " + yield_item.variable
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
        multi_query_clause_string = ""
        # with连接的查询部分
        for with_query_clause in multi_query_clause.with_query_clauses:
            if multi_query_clause_string != "":
                multi_query_clause_string = multi_query_clause_string + '\n'
            multi_query_clause_string = multi_query_clause_string + self.convert_with_query_clause(with_query_clause)
        # 最后一个查询部分
        if multi_query_clause_string != "":
            multi_query_clause_string = multi_query_clause_string + '\n'
        multi_query_clause_string = multi_query_clause_string + self.convert_single_query_clause(
            multi_query_clause.single_query_clause)
        # 更新可返回的变量名/别名
        self.variables_manager.variables_dict = {}
        return multi_query_clause_string

    def convert_with_query_clause(self, with_query_clause: WithQueryClause) -> str:
        with_query_clause_string = ""
        # reading_clauses部分
        for reading_clause in with_query_clause.reading_clauses:
            if with_query_clause_string != "":
                with_query_clause_string = with_query_clause_string + '\n'
            with_query_clause_string = with_query_clause_string + self.convert_reading_clause(reading_clause)
        # updating_clauses部分
        for updating_clause in with_query_clause.updating_clauses:
            if with_query_clause_string != "":
                with_query_clause_string = with_query_clause_string + '\n'
            with_query_clause_string = with_query_clause_string + self.convert_updating_clause(updating_clause)
        # with_clause部分
        if with_query_clause_string != "":
            with_query_clause_string = with_query_clause_string + '\n'
        with_query_clause_string = with_query_clause_string + self.convert_with_clause(with_query_clause.with_clause)
        return with_query_clause_string

    def convert_with_clause(self, with_clause: WithClause):
        self.is_with_or_return = True

        with_clause_string = "WITH "
        if with_clause.is_distinct:
            with_clause_string = "WITH DISTINCT "
        if with_clause.is_all:
            # 返回所有用户指定的可返回的变量名/别名
            for index, variable in enumerate(self.variables_manager.variables_dict.keys()):
                if index != 0:
                    with_clause_string = with_clause_string + ", "
                with_clause_string = with_clause_string + variable
        for projection_item in with_clause.projection_items:
            if with_clause_string not in ["WITH ", "WITH DISTINCT "]:
                with_clause_string = with_clause_string + ", "
            with_clause_string = with_clause_string + self.expression_converter.convert_expression(
                projection_item.expression)
            if projection_item.variable:
                with_clause_string = with_clause_string + " as " + projection_item.variable
        if with_clause.order_by_clause:
            with_clause_string = with_clause_string + '\n' + self.convert_order_by_clause(with_clause.order_by_clause)
        if with_clause.skip_expression:
            with_clause_string = with_clause_string + "\nSKIP " + self.expression_converter.convert_expression(
                with_clause.skip_expression)
        if with_clause.limit_expression:
            with_clause_string = with_clause_string + "\nLIMIT " + self.expression_converter.convert_expression(
                with_clause.limit_expression)

        unwind_clause_string = ""
        for index, (unwind_expression_string, unwind_variable) in enumerate(self.unwind_variables_dict.items()):
            unwind_clause_string = unwind_clause_string + "UNWIND " + unwind_expression_string + "\nAS " + unwind_variable + '\n'

        # 更新可返回的变量名/别名
        self.variables_manager.variables_dict = self.variables_manager.get_with_clause_variables_dict(with_clause)
        self.unwind_variables_dict = {}
        self.is_with_or_return = False
        return unwind_clause_string + with_clause_string

    def convert_single_query_clause(self, single_query_clause: SingleQueryClause) -> str:
        single_query_clause_string = ""
        # reading_clauses部分
        for reading_clause in single_query_clause.reading_clauses:
            if single_query_clause_string != "":
                single_query_clause_string = single_query_clause_string + '\n'
            single_query_clause_string = single_query_clause_string + self.convert_reading_clause(reading_clause)
        # updating_clauses部分
        for updating_clause in single_query_clause.updating_clauses:
            if single_query_clause_string != "":
                single_query_clause_string = single_query_clause_string + '\n'
            single_query_clause_string = single_query_clause_string + self.convert_updating_clause(updating_clause)
        # return_clause部分
        if single_query_clause.return_clause:
            if single_query_clause_string != "":
                single_query_clause_string = single_query_clause_string + '\n'
            single_query_clause_string = single_query_clause_string + self.convert_return_clause(
                single_query_clause.return_clause)
        return single_query_clause_string

    def convert_reading_clause(self, reading_clause: ReadingClause) -> str:
        # 更新可返回的变量名/别名
        self.variables_manager.variables_dict.update(
            self.variables_manager.get_reading_clause_variables_dict(reading_clause))
        reading_clause = reading_clause.reading_clause
        if reading_clause.__class__ == MatchClause:
            return self.convert_match_clause(reading_clause)
        elif reading_clause.__class__ == UnwindClause:
            # 更新可返回的变量名/别名
            return "UNWIND " + self.expression_converter.convert_expression(
                reading_clause.expression) + "\nAS " + reading_clause.variable
        elif reading_clause.__class__ == CallClause:
            return self.convert_call_clause(reading_clause)

    def convert_match_clause(self, match_clause: MatchClause) -> str:
        match_clause_string = "MATCH "
        if match_clause.is_optional:
            match_clause_string = "OPTIONAL MATCH "
        call_string = ""
        interval_conditions = []
        for pattern in match_clause.patterns:
            pattern = pattern.pattern
            if pattern.__class__ == SPath:
                path_pattern, property_patterns, path_interval_conditions = self.graph_converter.match_path(pattern,
                                                                                                            match_clause.time_window)
                if match_clause_string not in ["MATCH ", "OPTIONAL MATCH "]:
                    match_clause_string = match_clause_string + ", "
                match_clause_string = match_clause_string + path_pattern
                # 添加节点属性模式的匹配
                for property_pattern in property_patterns:
                    match_clause_string = match_clause_string + ", " + property_pattern
                interval_conditions.extend(path_interval_conditions)
            elif pattern.__class__ == TemporalPathCall:
                if call_string != "":
                    call_string = call_string + '\n'
                start_node_pattern, start_node_property_patterns, start_node_interval_conditions = self.graph_converter.match_object_node(
                    pattern.path.nodes[0], match_clause.time_window)
                end_node_pattern, end_node_property_patterns, end_node_interval_conditions = self.graph_converter.match_object_node(
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
                    interval_from_string = self.graph_converter.convert_time_point_literal(
                        pattern.path.edges[0].interval.interval_from)
                    interval_to_string = self.graph_converter.convert_time_point_literal(
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
        if match_clause_string not in ["MATCH ", "OPTIONAL MATCH "]:
            if call_string != "":
                match_clause_string = call_string + '\n' + match_clause_string
            if match_clause.where_expression or len(interval_conditions) != 0:
                where_string = self.convert_where_clause(match_clause.where_expression, interval_conditions)
                match_clause_string = match_clause_string + '\n' + where_string
            return match_clause_string
        else:
            return call_string

    def convert_where_clause(self, where_expression: Expression = None, interval_conditions: List[str] = None) -> str:
        if where_expression is None and (interval_conditions is None or len(interval_conditions) == 0):
            raise ValueError("The where expression and the interval conditions can't be None at the same time.")
        where_clause_string = "WHERE "
        if where_expression:
            where_clause_string = where_clause_string + self.expression_converter.convert_expression(where_expression)
        if interval_conditions:
            for interval_condition in interval_conditions:
                if where_clause_string != "WHERE ":
                    where_clause_string = where_clause_string + " and "
                where_clause_string = where_clause_string + interval_condition
        return where_clause_string

    def convert_updating_clause(self, updating_clause: UpdatingClause) -> str:
        updating_clause = updating_clause.updating_clause
        # 更新可返回的变量名/别名
        self.variables_manager.variables_dict.update(
            self.variables_manager.get_updating_clause_variables_dict(updating_clause))

        if updating_clause.__class__ == CreateClause:
            return self.convert_create_clause(updating_clause)
        elif updating_clause.__class__ == DeleteClause:
            return self.convert_delete_clause(updating_clause)
        elif updating_clause.__class__ == StaleClause:
            return self.convert_stale_clause(updating_clause)
        elif updating_clause.__class__ == SetClause:
            return self.convert_set_clause(updating_clause)
        elif updating_clause.__class__ == MergeClause:
            return self.convert_merge_clause(updating_clause)
        elif updating_clause.__class__ == RemoveClause:
            return self.convert_remove_clause(updating_clause)

    def convert_create_clause(self, create_clause: CreateClause) -> str:
        create_clause_string = "CREATE "
        for index, pattern in enumerate(create_clause.patterns):
            # create clause的pattern均为SPath类型
            pattern = pattern.pattern
            path_pattern, property_patterns = self.graph_converter.create_path(pattern, create_clause.at_time_clause)
            if index != 0:
                create_clause_string = create_clause_string + ", "
            create_clause_string = create_clause_string + path_pattern
            # 添加节点属性模式的匹配
            for property_pattern in property_patterns:
                create_clause_string = create_clause_string + ", " + property_pattern
        return create_clause_string

    def convert_delete_clause(self, delete_clause: DeleteClause) -> str:
        delete_clause_string = "DELETE "
        for delete_item in delete_clause.delete_items:
            if delete_item.property_name is None and delete_item.is_value is None:
                # 删除对象节点，以及相连的属性节点，值节点和边
                pass
            elif delete_item.property_name is not None and delete_item.is_value is None:
                # 删除属性节点，以及相连的值节点和边
                pass
            elif delete_item.property_name is not None and delete_item.is_value is not None:
                # 删除值节点，以及相连的边
                pass
        pass

    def convert_stale_clause(self, stale_clause: StaleClause) -> str:
        pass

    def convert_set_clause(self, set_clause: SetClause) -> str:
        pass

    def convert_merge_clause(self, merge_clause: MergeClause) -> str:
        pass

    def convert_remove_clause(self, remove_clause: RemoveClause) -> str:
        pass

    def convert_return_clause(self, return_clause: ReturnClause) -> str:
        self.is_with_or_return = True
        return_clause_string = "RETURN "
        if return_clause.is_distinct:
            return_clause_string = "RETURN DISTINCT "
        if return_clause.is_all:
            # 返回所有用户指定的可返回的变量
            for index, variable in enumerate(self.variables_manager.variables_dict.keys()):
                if index != 0:
                    return_clause_string = return_clause_string + ", "
                return_clause_string = return_clause_string + variable
        for projection_item in return_clause.projection_items:
            if return_clause_string not in ["RETURN ", "RETURN DISTINCT "]:
                return_clause_string = return_clause_string + ", "
            return_clause_string = return_clause_string + self.expression_converter.convert_expression(
                projection_item.expression)
            if projection_item.variable:
                return_clause_string = return_clause_string + " as " + projection_item.variable
        if return_clause.order_by_clause:
            return_clause_string = return_clause_string + '\n' + self.convert_order_by_clause(
                return_clause.order_by_clause)
        if return_clause.skip_expression:
            return_clause_string = return_clause_string + "\nSKIP " + self.expression_converter.convert_expression(
                return_clause.skip_expression)
        if return_clause.limit_expression:
            return_clause_string = return_clause_string + "\nLIMIT " + self.expression_converter.convert_expression(
                return_clause.limit_expression)

        unwind_clause_string = ""
        for index, (unwind_expression_string, unwind_variable) in enumerate(self.unwind_variables_dict.items()):
            unwind_clause_string = unwind_clause_string + "UNWIND " + unwind_expression_string + "\nAS " + unwind_variable + '\n'

        # 更新可返回的变量名/别名
        self.variables_manager.variables_dict = self.variables_manager.get_return_clause_variables_dict(return_clause)
        self.unwind_variables_dict = {}
        self.is_with_or_return = False
        return unwind_clause_string + return_clause_string

    def convert_order_by_clause(self, order_by_clause: OrderByClause) -> str:
        order_by_clause_string = ""
        for index, (key, value) in enumerate(order_by_clause.sort_items.items()):
            if index != 0:
                order_by_clause_string = order_by_clause_string + '\n'
            order_by_clause_string = order_by_clause_string + self.expression_converter.convert_expression(key)
            if value:
                order_by_clause_string = order_by_clause_string + ' ' + value
        return order_by_clause_string
