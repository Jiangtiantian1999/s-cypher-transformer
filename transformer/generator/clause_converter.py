from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.graph_converter import GraphConverter
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class ClauseConverter:

    @staticmethod
    def convert_union_query_clause(union_query_clause: UnionQueryClause, variables_manager: VariablesManager) -> str:
        union_query_string = ClauseConverter.convert_multi_query_clause(union_query_clause.multi_query_clauses[0],
                                                                        variables_manager)
        for index, is_all in enumerate(union_query_clause.is_all):
            if is_all:
                operator = " UNION ALL "
            else:
                operator = " UNION "
            union_query_string = union_query_string + '\n' + operator + ClauseConverter.convert_multi_query_clause(
                union_query_clause.multi_query_clauses[index + 1], variables_manager)
        return union_query_string

    @staticmethod
    def convert_call_clause(call_clause: CallClause, variables_manager: VariablesManager) -> str:
        if call_clause.procedure_name in GlobalVariables.scypher_procedure_info.keys():
            call_string = "CALL scypher." + call_clause.procedure_name
        else:
            call_string = "CALL " + call_clause.procedure_name
        input_string = ""
        for index, input_item in enumerate(call_clause.input_items):
            if index != 0:
                input_string = input_string + ", "
            input_item_string, input_item_type = ExpressionConverter.convert_expression(input_item, variables_manager)
            input_string = input_string + input_item_string
        call_string = call_string + '(' + input_string + ')'
        if call_clause.yield_clause:
            call_string = call_string + '\n' + ClauseConverter.convert_yield_clause(call_clause.yield_clause,
                                                                                    variables_manager)
        return call_string

    @staticmethod
    def convert_yield_clause(yield_clause: YieldClause, variables_manager: VariablesManager) -> str:
        # 更新可返回的变量名/别名
        variables_manager.variables_dict.update(variables_manager.get_yield_clause_variables_dict(yield_clause))
        yield_clause_string = "YIELD "
        for yield_item in yield_clause.yield_items:
            if yield_clause_string != "YIELD ":
                yield_clause_string = yield_clause_string + ", "
            yield_clause_string = yield_clause_string + yield_item.procedure_result
            if yield_item.variable:
                yield_clause_string = yield_clause_string + " as " + yield_item.variable
        if yield_clause.where_expression:
            where_expression_string, where_expression_type = ExpressionConverter.convert_expression(
                yield_clause.where_expression, variables_manager)
            yield_clause_string = yield_clause_string + "\nWHERE " + where_expression_string
        return yield_clause_string

    @staticmethod
    def convert_time_window_limit_clause(time_window_limit_clause: TimeWindowLimitClause,
                                         variables_manager: VariablesManager) -> str:
        time_window_limit = time_window_limit_clause.time_window_limit
        if time_window_limit.__class__ == SnapshotClause:
            time_window_limit_string, time_window_limit_type = ExpressionConverter.convert_expression(
                time_window_limit.time_point, variables_manager)
            return "CALL scypher.snapshot(" + time_window_limit_string + ')'
        elif time_window_limit.__class__ == ScopeClause:
            time_window_limit_string, time_window_limit_type = ExpressionConverter.convert_expression(
                time_window_limit.interval, variables_manager)
            return "CALL scypher.scope(" + time_window_limit_string + ')'

    @staticmethod
    def convert_multi_query_clause(multi_query_clause: MultiQueryClause, variables_manager: VariablesManager) -> str:
        multi_query_string = ""
        # with连接的查询部分
        for with_query_clause in multi_query_clause.with_query_clauses:
            if multi_query_string != "":
                multi_query_string = multi_query_string + '\n'
            multi_query_string = multi_query_string + ClauseConverter.convert_with_query_clause(with_query_clause,
                                                                                                variables_manager)
        # 最后一个查询部分
        if multi_query_string != "":
            multi_query_string = multi_query_string + '\n'
        multi_query_string = multi_query_string + ClauseConverter.convert_single_query_clause(
            multi_query_clause.single_query_clause, variables_manager)
        # 更新可返回的变量名/别名
        variables_manager.variables_dict = {}
        return multi_query_string

    @staticmethod
    def convert_with_query_clause(with_query_clause: WithQueryClause, variables_manager: VariablesManager) -> str:
        with_query_string = ""
        # reading_clauses部分
        for reading_clause in with_query_clause.reading_clauses:
            if with_query_string != "":
                with_query_string = with_query_string + '\n'
            with_query_string = with_query_string + ClauseConverter.convert_reading_clause(reading_clause,
                                                                                           variables_manager)
        # updating_clauses部分
        for updating_clause in with_query_clause.updating_clauses:
            if with_query_string != "":
                with_query_string = with_query_string + '\n'
            with_query_string = with_query_string + ClauseConverter.convert_updating_clause(updating_clause,
                                                                                            variables_manager)
        # with_clause部分
        if with_query_string != "":
            with_query_string = with_query_string + '\n'
        with_query_string = with_query_string + ClauseConverter.convert_with_clause(with_query_clause.with_clause,
                                                                                    variables_manager)
        return with_query_string

    @staticmethod
    def convert_with_clause(with_clause: WithClause, variables_manager: VariablesManager):
        with_clause_string = "WITH "
        if with_clause.is_distinct:
            with_clause_string = "WITH DISTINCT "
        for projection_item in with_clause.projection_items:
            if projection_item.is_all:
                # 返回所有用户指定的可返回的变量名/别名
                for variable in variables_manager.variables_dict.keys():
                    if with_clause_string not in ["WITH ", "WITH DISTINCT "]:
                        with_clause_string = with_clause_string + ", "
                    with_clause_string = with_clause_string + variable
            elif projection_item.expression:
                if with_clause_string not in ["WITH ", "WITH DISTINCT "]:
                    with_clause_string = with_clause_string + ", "
                projection_item_string, projection_item_type = ExpressionConverter.convert_expression(
                    projection_item.expression, variables_manager)
                with_clause_string = with_clause_string + projection_item_string
                if projection_item.variable:
                    with_clause_string = with_clause_string + " as " + projection_item.variable
        if with_clause.order_by_clause:
            with_clause_string = with_clause_string + '\n' + ClauseConverter.convert_order_by_clause(
                with_clause.order_by_clause, variables_manager)
        if with_clause.skip_expression:
            skip_expression_string, skip_expression_type = ExpressionConverter.convert_expression(
                with_clause.skip_expression, variables_manager)
            with_clause_string = with_clause_string + "\nSKIP " + skip_expression_string
        if with_clause.limit_expression:
            limit_expression_string, limit_expression_type = ExpressionConverter.convert_expression(
                with_clause.limit_expression, variables_manager)
            with_clause_string = with_clause_string + "\nLIMIT " + limit_expression_string

        match_clause_string = ""
        if len(variables_manager.with_project_items) != 0:
            match_clause_string = "WITH *"
            for with_project_item in variables_manager.with_project_items:
                match_clause_string = match_clause_string + ", " + with_project_item
            match_clause_string = match_clause_string + '\n'
        if len(variables_manager.property_patterns) != 0:
            match_clause_string = match_clause_string + "MATCH "
            for index, property_pattern in enumerate(variables_manager.property_patterns):
                if index != 0:
                    match_clause_string = match_clause_string + ", "
                match_clause_string = match_clause_string + property_pattern
            match_clause_string = match_clause_string + '\n'

        # 更新可返回的变量名/别名
        variables_manager.variables_dict = variables_manager.get_with_clause_variables_dict(with_clause)
        variables_manager.property_patterns, variables_manager.with_project_items = [], []
        return match_clause_string + with_clause_string

    @staticmethod
    def convert_single_query_clause(single_query_clause: SingleQueryClause, variables_manager: VariablesManager) -> str:
        single_query_string = ""
        # reading_clauses部分
        for reading_clause in single_query_clause.reading_clauses:
            if single_query_string != "":
                single_query_string = single_query_string + '\n'
            single_query_string = single_query_string + ClauseConverter.convert_reading_clause(reading_clause,
                                                                                               variables_manager)
        # updating_clauses部分
        for updating_clause in single_query_clause.updating_clauses:
            if single_query_string != "":
                single_query_string = single_query_string + '\n'
            single_query_string = single_query_string + ClauseConverter.convert_updating_clause(updating_clause,
                                                                                                variables_manager)
        # return_clause部分
        if single_query_clause.return_clause:
            if single_query_string != "":
                single_query_string = single_query_string + '\n'
            single_query_string = single_query_string + ClauseConverter.convert_return_clause(
                single_query_clause.return_clause, variables_manager)
        return single_query_string

    @staticmethod
    def convert_reading_clause(reading_clause: ReadingClause, variables_manager: VariablesManager) -> str:
        # 更新可返回的变量名/别名
        variables_manager.variables_dict.update(variables_manager.get_reading_clause_variables_dict(reading_clause))
        reading_clause = reading_clause.reading_clause
        if reading_clause.__class__ == MatchClause:
            return ClauseConverter.convert_match_clause(reading_clause, variables_manager)
        elif reading_clause.__class__ == UnwindClause:
            # 更新可返回的变量名/别名
            expression_string, expression_type = ExpressionConverter.convert_expression(
                reading_clause.expression, variables_manager)
            return "UNWIND " + expression_string + " AS " + reading_clause.variable
        elif reading_clause.__class__ == CallClause:
            return ClauseConverter.convert_call_clause(reading_clause, variables_manager)

    @staticmethod
    def convert_match_clause(match_clause: MatchClause, variables_manager: VariablesManager) -> str:
        match_string = "MATCH "
        if match_clause.is_optional:
            match_string = "OPTIONAL MATCH "
        call_string = ""
        interval_conditions = []
        for pattern in match_clause.patterns:
            pattern = pattern.pattern
            if pattern.__class__ == SPath:
                path_pattern, property_patterns, path_interval_conditions = GraphConverter.convert_path(pattern,
                                                                                                        match_clause.time_window,
                                                                                                        variables_manager)
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
                start_node_pattern, start_node_property_patterns, start_node_interval_conditions = GraphConverter.convert_object_node(
                    pattern.path.nodes[0], match_clause.time_window, variables_manager)
                end_node_pattern, end_node_property_patterns, end_node_interval_conditions = GraphConverter.convert_object_node(
                    pattern.path.nodes[1], match_clause.time_window, variables_manager)
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
                    interval_from_string = GraphConverter.convert_time_point_literal(
                        pattern.path.edges[0].interval.interval_from)
                    interval_to_string = GraphConverter.convert_time_point_literal(
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
                where_string = ClauseConverter.convert_where_clause(match_clause.where_expression, interval_conditions,
                                                                    variables_manager)
                match_string = match_string + '\n' + where_string
            return match_string
        else:
            return call_string

    @staticmethod
    def convert_where_clause(where_expression: Expression = None, interval_conditions: List[str] = None,
                             variables_manager: VariablesManager = None) -> str:
        if where_expression is None and (interval_conditions is None or len(interval_conditions) == 0):
            raise ValueError("The where expression and the interval conditions can't be None at the same time.")
        where_clause_string = "WHERE "
        if where_expression:
            where_expression_string, where_expression_type = ExpressionConverter.convert_expression(where_expression,
                                                                                                    variables_manager)
            where_clause_string = where_clause_string + where_expression_string
        if interval_conditions:
            for interval_condition in interval_conditions:
                if where_clause_string != "WHERE ":
                    where_clause_string = where_clause_string + " and "
                where_clause_string = where_clause_string + interval_condition
        
        match_clause_string = ""
        if len(variables_manager.with_project_items) != 0:
            match_clause_string = "WITH *"
            for with_project_item in variables_manager.with_project_items:
                match_clause_string = match_clause_string + ", " + with_project_item
            match_clause_string = match_clause_string + '\n'
        if len(variables_manager.property_patterns) != 0:
            match_clause_string = match_clause_string + "MATCH "
            for index, property_pattern in enumerate(variables_manager.property_patterns):
                if index != 0:
                    match_clause_string = match_clause_string + ", "
                match_clause_string = match_clause_string + property_pattern
            match_clause_string = match_clause_string + '\n'

        variables_manager.property_patterns, variables_manager.with_project_items = [], []
        return match_clause_string + where_clause_string

    @staticmethod
    def convert_updating_clause(updating_clause: UpdatingClause, variables_manager: VariablesManager) -> str:
        # 更新可返回的变量名/别名
        variables_manager.variables_dict.update(variables_manager.get_updating_clause_variables_dict(updating_clause))
        pass

    @staticmethod
    def convert_return_clause(return_clause: ReturnClause, variables_manager: VariablesManager) -> str:
        return_clause_string = "RETURN "
        if return_clause.is_distinct:
            return_clause_string = "RETURN DISTINCT "
        for projection_item in return_clause.projection_items:
            if projection_item.is_all:
                # 返回所有用户指定的可返回的变量
                for variable in variables_manager.variables_dict.keys():
                    if return_clause_string not in ["RETURN ", "RETURN DISTINCT "]:
                        return_clause_string = return_clause_string + ", "
                    return_clause_string = return_clause_string + variable
            elif projection_item.expression:
                if return_clause_string not in ["RETURN ", "RETURN DISTINCT "]:
                    return_clause_string = return_clause_string + ", "
                projection_item_string, projection_item_type = ExpressionConverter.convert_expression(
                    projection_item.expression, variables_manager)
                return_clause_string = return_clause_string + projection_item_string
                if projection_item.variable:
                    return_clause_string = return_clause_string + " as " + projection_item.variable
        if return_clause.order_by_clause:
            return_clause_string = return_clause_string + '\n' + ClauseConverter.convert_order_by_clause(
                return_clause.order_by_clause, variables_manager)
        if return_clause.skip_expression:
            skip_expression_string, skip_expression_type = ExpressionConverter.convert_expression(
                return_clause.skip_expression, variables_manager)
            return_clause_string = return_clause_string + "\nSKIP " + skip_expression_string
        if return_clause.limit_expression:
            limit_expression_string, limit_expression_type = ExpressionConverter.convert_expression(
                return_clause.limit_expression, variables_manager)
            return_clause_string = return_clause_string + "\nLIMIT " + limit_expression_string

        match_clause_string = ""
        if len(variables_manager.with_project_items) != 0:
            match_clause_string = "WITH *"
            for with_project_item in variables_manager.with_project_items:
                match_clause_string = match_clause_string + ", " + with_project_item
            match_clause_string = match_clause_string + '\n'
        if len(variables_manager.property_patterns) != 0:
            match_clause_string = match_clause_string + "MATCH "
            for index, property_pattern in enumerate(variables_manager.property_patterns):
                if index != 0:
                    match_clause_string = match_clause_string + ", "
                match_clause_string = match_clause_string + property_pattern
            match_clause_string = match_clause_string + '\n'

        # 更新可返回的变量名/别名
        variables_manager.variables_dict = variables_manager.get_return_clause_variables_dict(return_clause)
        variables_manager.property_patterns, variables_manager.with_project_items = [], []
        return match_clause_string + return_clause_string

    @staticmethod
    def convert_order_by_clause(order_by_clause: OrderByClause, variables_manager: VariablesManager) -> str:
        order_by_clause_string = ""
        for index, (key, value) in enumerate(order_by_clause.sort_items.items()):
            if index != 0:
                order_by_clause_string = order_by_clause_string + '\n'
            expression_string, expression_type = ExpressionConverter.convert_expression(key, variables_manager)
            order_by_clause_string = order_by_clause_string + expression_string
            if value:
                order_by_clause_string = order_by_clause_string + ' ' + value
        return order_by_clause_string
