from transformer.conf.config_reader import ConfigReader
from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.graph_converter import GraphConverter
from transformer.generator.utils import convert_dict_to_str
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *


class ClauseConverter:
    def __init__(self, variables_manager: VariablesManager, expression_converter: ExpressionConverter,
                 graph_converter: GraphConverter):
        self.variables_manager = variables_manager
        self.expression_converter = expression_converter
        self.graph_converter = graph_converter

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
        for input_item in call_clause.input_items:
            input_string = input_string + self.expression_converter.convert_expression(input_item) + ", "
        call_clause_string = call_clause_string + '(' + input_string.rstrip(", ") + ')'

        if call_clause.yield_clause:
            call_clause_string = call_clause_string + '\n' + self.convert_yield_clause(call_clause.yield_clause)

        return call_clause_string

    def convert_yield_clause(self, yield_clause: YieldClause) -> str:
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
            where_clause_string = "WHERE " + self.expression_converter.convert_expression(yield_clause.where_expression)
            yield_clause_string = yield_clause_string + '\n' + where_clause_string

        return yield_clause_string

    def convert_time_window_limit_clause(self, time_window_limit_clause: TimeWindowLimitClause) -> str:
        time_window_limit = time_window_limit_clause.time_window_limit
        if time_window_limit.__class__ == SnapshotClause:
            time_point_expression_string = self.expression_converter.convert_expression(time_window_limit.time_point)
            return "CALL scypher.snapshot(" + time_point_expression_string + ')'
        elif time_window_limit.__class__ == ScopeClause:
            interval_expression_string = self.expression_converter.convert_expression(time_window_limit.interval)
            return "CALL scypher.scope(" + interval_expression_string + ')'

    def convert_multi_query_clause(self, multi_query_clause: MultiQueryClause) -> str:
        multi_query_clause_string = ""
        # with连接的查询部分
        for with_query_clause in multi_query_clause.with_query_clauses:
            with_query_clause_string = self.convert_with_query_clause(with_query_clause)
            multi_query_clause_string = multi_query_clause_string + with_query_clause_string + '\n'
        # 最后一个查询部分
        multi_query_clause_string = multi_query_clause_string + self.convert_single_query_clause(
            multi_query_clause.single_query_clause)
        return multi_query_clause_string

    def convert_with_query_clause(self, with_query_clause: WithQueryClause) -> str:
        # reading_clauses部分
        reading_clause_string = ""
        for reading_clause in with_query_clause.reading_clauses:
            reading_clause_string = reading_clause_string + self.convert_reading_clause(reading_clause) + '\n'
        # updating_clauses部分
        updating_clause_string = ""
        for updating_clause in with_query_clause.updating_clauses:
            updating_clause_string = updating_clause_string + self.convert_updating_clause(updating_clause) + '\n'
        # with_clause部分
        with_clause_string = self.convert_with_clause(with_query_clause.with_clause)

        return reading_clause_string + updating_clause_string + with_clause_string

    def convert_with_clause(self, with_clause: WithClause):
        with_clause_string = "WITH "
        if with_clause.is_distinct:
            with_clause_string = "WITH DISTINCT "
        if with_clause.is_all:
            with_clause_string = with_clause_string + "*, "
        for projection_item in with_clause.projection_items:
            projection_item_expression_string = self.expression_converter.convert_expression(projection_item.expression)
            with_clause_string = with_clause_string + projection_item_expression_string
            if projection_item.variable:
                with_clause_string = with_clause_string + " as " + projection_item.variable
            with_clause_string = with_clause_string + ", "
        with_clause_string = with_clause_string.rstrip(", ")

        if with_clause.order_by_clause:
            with_clause_string = with_clause_string + '\n' + self.convert_order_by_clause(with_clause.order_by_clause)
        if with_clause.skip_expression:
            skip_expression_string = self.expression_converter.convert_expression(with_clause.skip_expression)
            with_clause_string = with_clause_string + "\nSKIP " + skip_expression_string
        if with_clause.limit_expression:
            limit_expression_string = self.expression_converter.convert_expression(with_clause.limit_expression)
            with_clause_string = with_clause_string + "\nLIMIT " + limit_expression_string

        return with_clause_string

    def convert_single_query_clause(self, single_query_clause: SingleQueryClause) -> str:
        # reading_clauses部分
        reading_clause_string = ""
        for reading_clause in single_query_clause.reading_clauses:
            reading_clause_string = reading_clause_string + self.convert_reading_clause(reading_clause) + '\n'
        # updating_clauses部分
        updating_clause_string = ""
        for updating_clause in single_query_clause.updating_clauses:
            updating_clause_string = updating_clause_string + self.convert_updating_clause(updating_clause) + '\n'
        # return_clause部分
        return_clause_string = ""
        if single_query_clause.return_clause:
            return_clause_string = self.convert_return_clause(single_query_clause.return_clause)
        return (reading_clause_string + updating_clause_string + return_clause_string).rstrip()

    def convert_reading_clause(self, reading_clause: ReadingClause) -> str:
        if reading_clause.reading_clause.__class__ == MatchClause:
            return self.convert_match_clause(reading_clause.reading_clause)
        elif reading_clause.reading_clause.__class__ == UnwindClause:
            unwind_expression_string = self.expression_converter.convert_expression(
                reading_clause.reading_clause.expression)
            return "UNWIND" + unwind_expression_string + "\nAS " + reading_clause.reading_clause.variable
        elif reading_clause.reading_clause.__class__ == CallClause:
            return self.convert_call_clause(reading_clause.reading_clause)

    def convert_match_clause(self, match_clause: MatchClause) -> str:
        match_clause_string = "MATCH "
        if match_clause.is_optional:
            match_clause_string = "OPTIONAL MATCH "
        pattern_interval_info = {}
        call_string = ""
        for pattern in match_clause.patterns:
            pattern = pattern.pattern
            if pattern.__class__ == SPath:
                path_pattern, property_patterns, path_interval_info = self.graph_converter.match_path(pattern,
                                                                                                      match_clause.time_window)
                match_clause_string = match_clause_string + path_pattern + ", "
                for property_pattern in property_patterns:
                    match_clause_string = match_clause_string + property_pattern + ", "
                # 添加路径的时态条件限制
                pattern_interval_info.update(path_interval_info)
            elif pattern.__class__ == TemporalPathCall:
                if pattern.path.edges[0].direction == SEdge.LEFT:
                    start_node, end_node = pattern.path.nodes[1], pattern.path.nodes[0]
                else:
                    start_node, end_node = pattern.path.nodes[0], pattern.path.nodes[1]
                start_node_pattern, start_node_property_patterns, start_node_interval_info = self.graph_converter.match_object_node(
                    start_node, match_clause.time_window)
                end_node_pattern, end_node_property_patterns, end_node_interval_info = self.graph_converter.match_object_node(
                    end_node, match_clause.time_window)
                call_string = call_string + "\nMATCH " + start_node_pattern + ", " + end_node_pattern
                # 添加节点属性模式的匹配
                for property_pattern in start_node_property_patterns + end_node_property_patterns:
                    call_string = call_string + ", " + property_pattern
                # 限制节点的有效时间
                temporal_path_interval_info = start_node_interval_info
                temporal_path_interval_info.update(end_node_interval_info)
                if len(temporal_path_interval_info) > 0 or match_clause.time_window:
                    where_expression_string = self.convert_where_clause(None, temporal_path_interval_info,
                                                                        match_clause.time_window)
                    call_string = call_string + '\n' + where_expression_string
                edge_info = {}
                # 限制路径的标签
                if len(pattern.path.edges[0].labels) != 0:
                    edge_info["labels"] = pattern.path.edges[0].labels
                # 限制路径的长度
                if pattern.path.edges[0].length[0] is not None:
                    edge_info["minLength"] = pattern.path.edges[0].length[0]
                if pattern.path.edges[0].length[1] is not None:
                    edge_info["maxLength"] = pattern.path.edges[0].length[1]
                # 限制路径的有效时间
                if pattern.path.edges[0].time_window:
                    edge_info[
                        "effectiveTime"] = self.expression_converter.convert_at_t_element(
                        pattern.path.edges[0].time_window)
                elif match_clause.time_window:
                    if match_clause.time_window.__class__ == AtTimeClause:
                        edge_info["effectiveTime"] = self.expression_converter.convert_expression(
                            match_clause.time_window.time_point)
                    elif match_clause.time_window.time_point == BetweenClause:
                        edge_info["effectiveTime"] = self.expression_converter.convert_expression(
                            match_clause.time_window.interval)
                # 限制路径的属性
                if len(pattern.path.edges[0].properties) != 0:
                    edge_info["properties"] = {}
                    for property_name, property_value in pattern.path.edges[0].properties.items():
                        edge_info["properties"][property_name] = self.expression_converter.convert_expression(
                            property_value)

                call_string = call_string + "\nCALL scypher." + pattern.function_name + '(' + start_node.variable + ", " + end_node.variable + ", " + convert_dict_to_str(
                    edge_info) + ")\nYIELD " + pattern.variable

        if match_clause_string in ["MATCH ", "OPTIONAL MATCH "]:
            return call_string
        match_clause_string.rstrip(", ")

        if match_clause.where_expression or len(pattern_interval_info) != 0 or match_clause.time_window:
            where_expression_string = self.convert_where_clause(match_clause.where_expression, pattern_interval_info,
                                                                match_clause.time_window)
            match_clause_string = match_clause_string + '\n' + where_expression_string

        return match_clause_string + call_string

    def convert_where_clause(self, where_expression: Expression = None,
                             path_interval_info: dict[str, str] = None,
                             time_window: AtTimeClause | BetweenClause = None) -> str:
        if where_expression is None and (
                path_interval_info is None or len(path_interval_info) == 0) and time_window is None:
            raise ValueError("The where expression and the interval conditions can't be None at the same time.")
        where_clause_string = "WHERE "
        if where_expression:
            where_clause_string = where_clause_string + self.expression_converter.convert_expression(where_expression)
        if path_interval_info or time_window:
            if where_clause_string != "WHERE ":
                where_clause_string = where_clause_string + " and "
            if time_window.__class__ == AtTimeClause:
                time_window_string = self.expression_converter.convert_expression(time_window.time_point)
            elif time_window.__class__ == BetweenClause:
                time_window_string = self.expression_converter.convert_expression(time_window.interval)
            else:
                time_window_string = "NULL"
            where_clause_string = where_clause_string + "scypher.limitEffectiveTime(" + convert_dict_to_str(
                path_interval_info) + ", " + time_window_string + ')'

        return where_clause_string

    def convert_updating_clause(self, updating_clause: UpdatingClause) -> str:
        if updating_clause.updating_clause.__class__ == CreateClause:
            return self.convert_create_clause(updating_clause.updating_clause)
        elif updating_clause.updating_clause.__class__ == DeleteClause:
            return self.convert_delete_clause(updating_clause.updating_clause)
        elif updating_clause.updating_clause.__class__ == StaleClause:
            return self.convert_stale_clause(updating_clause.updating_clause)
        elif updating_clause.updating_clause.__class__ == SetClause:
            return self.convert_set_clause(updating_clause.updating_clause)
        elif updating_clause.updating_clause.__class__ == MergeClause:
            return self.convert_merge_clause(updating_clause.updating_clause)
        elif updating_clause.updating_clause.__class__ == RemoveClause:
            return self.convert_remove_clause(updating_clause.updating_clause)

    def convert_create_clause(self, create_clause: CreateClause) -> str:
        create_clause_string = ""
        for pattern in create_clause.patterns:
            # create clause的pattern均为SPath类型
            pattern = pattern.pattern
            if create_clause_string == "":
                create_clause_string = "CREATE "
            else:
                create_clause_string = create_clause_string + "\nCREATE "
            object_node_patterns, property_node_patterns, value_node_patterns, path_pattern = self.graph_converter.create_path(
                pattern, create_clause.at_time_clause)
            if len(object_node_patterns) == 1 and path_pattern:
                create_clause_string = create_clause_string + path_pattern
            else:
                for object_node_pattern in object_node_patterns:
                    create_clause_string = create_clause_string + object_node_pattern + ", "
                create_clause_string = create_clause_string.rstrip(", ")
            if len(property_node_patterns) > 0:
                create_clause_string = create_clause_string + "\nCREATE"
                for property_node_pattern in property_node_patterns:
                    create_clause_string = create_clause_string + property_node_pattern + ", "
                create_clause_string = create_clause_string.rstrip(", ")
            if len(value_node_patterns) > 0:
                create_clause_string = create_clause_string + "\nCREATE"
                for value_node_pattern in value_node_patterns:
                    create_clause_string = create_clause_string + value_node_pattern + ", "
                create_clause_string = create_clause_string.rstrip(", ")
            if len(object_node_patterns) > 1 and path_pattern:
                create_clause_string = create_clause_string + "\nCREATE " + path_pattern
        return create_clause_string

    def convert_delete_clause(self, delete_clause: DeleteClause) -> str:
        delete_clause_string = ""

        for delete_item in delete_clause.delete_items:
            if delete_item.property_value_at_t_element is None:
                # 物理删除对象节点/路径/边，调用scypher.getItemToDelete，参数为对象节点/路径/边
                # 删除对象节点/路径时，返回已删除了属性节点和值节点的对象节点/路径；删除边时，返回边。
                delete_clause_string = delete_clause_string + "\nDELETE "
                if delete_clause.is_detach:
                    delete_clause_string = delete_clause_string + "\nDETACH DELETE "
                delete_clause_string = delete_clause_string + "scypher.getObjectToDelete(" + self.expression_converter.convert_expression(
                    delete_item.expression) + ")"
            else:
                # 删除对象节点的属性，第一个参数为对象节点，第二个参数为属性名，第三个参数为删除的值节点的范围
                # 以列表形式返回所有待物理删除的元素
                delete_list_string = "scypher.getItemToDelete(" + self.expression_converter.convert_expression(
                    delete_item.expression) + ", "
                delete_list_string = delete_list_string + delete_item.property_value_at_t_element.property_name + ", "
                if delete_item.property_value_at_t_element.time_window:
                    if delete_item.property_value_at_t_element.time_window.__class__ == AtTElement:
                        delete_list_string = delete_list_string + self.expression_converter.convert_at_t_element(
                            delete_item.property_value_at_t_element.time_window) + ')'
                    else:
                        delete_list_string = delete_list_string + str(
                            delete_item.property_value_at_t_element.time_window) + ')'
                else:
                    delete_list_string = delete_list_string + "NULL)"
                delete_item_variable = self.variables_manager.get_random_variable()
                delete_clause_string = delete_clause_string + "\nFOREACH (" + delete_item_variable + " IN " + delete_list_string + " | DELETE " + delete_item_variable + ')'

        return delete_clause_string.lstrip()

    def convert_stale_clause(self, stale_clause: StaleClause) -> str:
        stale_clause_string = "FOREACH "
        stale_list_string = ""
        for stale_item in stale_clause.stale_items:
            # 逻辑删除对象节点/属性节点/值节点/边，调用scypher.getItemToStale，第一个参数为对象节点，第二个参数为属性名，第三个参数为【是否仅逻辑删除值节点】，第四个参数为逻辑删除时间
            # 以列表形式返回所有待逻辑删除的元素
            stale_list_string = stale_list_string + "scypher.getItemToStale(" + self.expression_converter.convert_expression(
                stale_item.expression)
            if stale_item.property_name:
                stale_list_string = stale_list_string + ", " + stale_item.property_name
            else:
                stale_list_string = stale_list_string + ", NULL"
            stale_list_string = stale_list_string + ", " + str(stale_item.is_value) + ") + "

        stale_list_string = stale_list_string.rstrip(" + ")
        stale_item_variable = self.variables_manager.get_random_variable()
        stale_clause_string = stale_clause_string + " (" + stale_item_variable + " IN " + stale_list_string + " | SET " + stale_item_variable + ".intervalTo = "

        if stale_clause.at_time_clause:
            stale_clause_string = stale_clause_string + self.expression_converter.convert_expression(
                stale_clause.at_time_clause.time_point) + ')'
        else:
            stale_clause_string = stale_clause_string + "scypher.operateTime())"

        return stale_clause_string.rstrip(", ")

    def convert_set_clause(self, set_clause: SetClause) -> str:
        set_clause_string = ""
        if set_clause.at_time_clause:
            time_point = self.expression_converter.convert_expression(set_clause.at_time_clause.time_point)
        else:
            time_point = "NULL"
        for set_item in set_clause.set_items:
            # 为在set时检查约束，调用scypher.getItemToSetX
            if set_item.__class__ == IntervalSetting:
                # 设置对象节点/属性节点/值节点/边的有效时间，调用scypher.getItemToSetInterval，第一个参数为对象节点，第二个参数为属性名，第三个参数为值节点有效时间，第四个参数为被设置的有效时间
                set_item_variable = self.variables_manager.get_random_variable()
                set_clause_string = set_clause_string + "\nFOREACH (" + set_item_variable + " IN scypher.getItemToSetInterval(" + set_item.object_variable + ", "
                if set_item.property_value_at_t_element:
                    set_clause_string = set_clause_string + set_item.property_value_at_t_element.property_name + ", "
                else:
                    set_clause_string = set_clause_string + "NULL, "
                if set_item.property_value_at_t_element.time_window and set_item.property_value_at_t_element.time_window.__class__ == AtTElement:
                    set_clause_string = set_clause_string + self.expression_converter.convert_at_t_element(
                        set_item.property_value_at_t_element.time_window) + ", "
                else:
                    set_clause_string = set_clause_string + "NULL, "
                set_clause_string = set_clause_string + self.expression_converter.convert_expression(
                    set_item.interval) + ')'
                set_clause_string = set_clause_string + " | SET " + set_item_variable + ".left = " + set_item_variable + ".right)"
            elif set_item.__class__ == ExpressionSetting:
                # 修改节点/边的属性，调用scypher.getItemToSetExpression，第一个参数为对象节点，第二个参数为属性名，
                # 第三个参数为set的操作时间，第四个参数为【是否为+=】，第五个参数为表达式
                set_item_variable = self.variables_manager.get_random_variable()
                set_clause_string = set_clause_string + "\nFOREACH (" + set_item_variable + " IN scypher.getItemToSetExpression("
                if set_item.expression_left.__class__ == SetPropertyExpression:
                    object_variable = self.expression_converter.convert_atom(set_item.expression_left.atom)
                    for index, property_lookup in enumerate(set_item.expression_left.property_chains):
                        if index != len(set_item.expression_left.property_chains) - 1:
                            object_variable = self.expression_converter.get_property_value(object_variable,
                                                                                           property_lookup.property_name,
                                                                                           property_lookup.time_window)
                    set_clause_string = set_clause_string + object_variable + ", "
                    if len(set_item.expression_left.property_chains) > 0:
                        property_lookup = set_item.expression_left.property_chains[-1]
                        set_clause_string = set_clause_string + property_lookup.property_name + ", "
                        if property_lookup.time_window:
                            set_clause_string = set_clause_string + self.expression_converter.convert_at_t_element(
                                property_lookup.time_window) + ", "
                        else:
                            set_clause_string = set_clause_string + time_point + ", "
                    else:
                        set_clause_string = set_clause_string + "NULL, " + time_point + ", "
                else:
                    set_clause_string = set_clause_string + set_item.expression_left + ", NULL" + time_point + ", "
                set_clause_string = set_clause_string + str(
                    set_item.is_added) + ", " + self.expression_converter.convert_expression(
                    set_item.expression_right) + ')'
                set_clause_string = set_clause_string + " | SET " + set_item_variable + ".left = " + set_item_variable + ".right)"
            else:
                # 设置节点/边的标签
                set_clause_string = set_clause_string + "\nSET " + set_item.variable
                for label in set_item.labels:
                    set_clause_string = set_clause_string + ':' + label

        return set_clause_string.lstrip()

    def convert_merge_clause(self, merge_clause: MergeClause) -> str:
        merge_clause_string = "MERGE "
        object_node_patterns, property_node_patterns, value_node_patterns, path_pattern = self.graph_converter.create_path(
            merge_clause.pattern, merge_clause.at_time_clause)
        if len(object_node_patterns) == 1 and path_pattern:
            # merge一条长度为0的路径
            merge_clause_string = merge_clause_string + path_pattern
        else:
            # merge一条长度>0的路径，先merge对象节点
            for object_node_pattern in object_node_patterns:
                merge_clause_string = merge_clause_string + object_node_pattern + ", "
            merge_clause_string = merge_clause_string.rstrip(", ")
        if len(property_node_patterns) > 0:
            # merge属性节点
            merge_clause_string = merge_clause_string + "\nMERGE"
            for property_node_pattern in property_node_patterns:
                merge_clause_string = merge_clause_string + property_node_pattern + ", "
            merge_clause_string = merge_clause_string.rstrip(", ")
        if len(value_node_patterns) > 0:
            # merge值节点
            merge_clause_string = merge_clause_string + "\nMERGE"
            for value_node_pattern in value_node_patterns:
                merge_clause_string = merge_clause_string + value_node_pattern + ", "
            merge_clause_string = merge_clause_string.rstrip(", ")
        if len(object_node_patterns) > 1 and path_pattern:
            # 当路径长度>0时，merge路径（创建对象节点之间的边）
            merge_clause_string = merge_clause_string + "\nMERGE" + path_pattern

        for action, set_clause in merge_clause.actions.items():
            merge_clause_string = merge_clause_string + '\n' + action + ' ' + self.convert_set_clause(set_clause) + '\n'

        return merge_clause_string.rstrip()

    def convert_remove_clause(self, remove_clause: RemoveClause) -> str:
        remove_clause_string = "REMOVE "
        for remove_item in remove_clause.remove_items:
            if remove_item.__class__ == LabelSetting:
                remove_clause_string = remove_clause_string + remove_item.variable
                for label in remove_item.labels:
                    remove_clause_string = remove_clause_string + ':' + label
            else:
                # 移除边的属性
                edge_variable = self.expression_converter.convert_atom(remove_item.atom)
                for property_lookup in remove_item.property_chains:
                    edge_variable = self.expression_converter.get_property_value(edge_variable,
                                                                                 property_lookup.property_name,
                                                                                 property_lookup.time_window)
                remove_clause_string = remove_clause_string + edge_variable + '.' + remove_item.property_name
            remove_clause_string = remove_clause_string + ", "
        return remove_clause_string.rstrip(", ")

    def convert_return_clause(self, return_clause: ReturnClause) -> str:
        return_clause_string = "RETURN "
        if return_clause.is_distinct:
            return_clause_string = "RETURN DISTINCT "
        if return_clause.is_all:
            property_item_expression_string_list = []
            for property_item in return_clause.projection_items:
                property_item_expression_string_list.append(
                    self.expression_converter.convert_expression(property_item.expression))
            # 返回所有用户指定的可返回的变量
            for variable in self.variables_manager.user_variables:
                if variable not in property_item_expression_string_list:
                    return_clause_string = return_clause_string + variable + ", "
            return_clause_string.rstrip(", ")
        for index, projection_item in enumerate(return_clause.projection_items):
            if index != 0:
                return_clause_string = return_clause_string + ", "
            projection_item_expression_string = self.expression_converter.convert_expression(projection_item.expression)
            return_clause_string = return_clause_string + projection_item_expression_string
            if projection_item.variable:
                return_clause_string = return_clause_string + " as " + projection_item.variable

        if return_clause.order_by_clause:
            order_by_clause_string = self.convert_order_by_clause(return_clause.order_by_clause)
            return_clause_string = return_clause_string + '\n' + order_by_clause_string
        if return_clause.skip_expression:
            skip_expression_string = self.expression_converter.convert_expression(return_clause.skip_expression)
            return_clause_string = return_clause_string + "\nSKIP " + skip_expression_string
        if return_clause.limit_expression:
            limit_expression_string = self.expression_converter.convert_expression(return_clause.limit_expression)
            return_clause_string = return_clause_string + "\nLIMIT " + limit_expression_string

        return return_clause_string

    def convert_order_by_clause(self, order_by_clause: OrderByClause) -> str:
        order_by_clause_string = "ORDER BY "
        for index, (expression, sort_method) in enumerate(order_by_clause.sort_items.items()):
            if index != 0:
                order_by_clause_string = order_by_clause_string + '\n'
            order_by_clause_string = order_by_clause_string + self.expression_converter.convert_expression(expression)
            if sort_method:
                order_by_clause_string = order_by_clause_string + ' ' + sort_method
        return order_by_clause_string
