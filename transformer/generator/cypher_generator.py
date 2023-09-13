from typing import List

from transformer.ir.s_clause_component import *
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_expression import *
from transformer.ir.s_graph import SEdge, SNode, ObjectNode, SPath


class CypherGenerator:
    count_num = 999
    # 原句里自带的变量名
    variables_dict = []
    s_cypher_clause = None

    # 获取新的变量名
    def get_random_variable(self) -> str:
        self.count_num = self.count_num + 1
        while 'var' + str(self.count_num) in self.variables_dict.keys():
            self.count_num = self.count_num + 1
        return 'var' + str(self.count_num)

    def generate_cypher_query(self, s_cypher_clause: SCypherClause) -> str:
        self.count_num = 999
        self.variables_dict = s_cypher_clause.get_variables_dict()
        self.s_cypher_clause = s_cypher_clause
        if s_cypher_clause.query_clause.__class__ == UnionQueryClause:
            return self.convert_union_query_clause(s_cypher_clause.query_clause)
        elif s_cypher_clause.query_clause.__class__ == CallClause:
            return self.convert_call_clause(s_cypher_clause.query_clause)
        elif s_cypher_clause.query_clause.__class__ == TimeWindowLimitClause:
            return self.convert_time_window_limit_clause(s_cypher_clause.query_clause)

    def convert_union_query_clause(self, s_cypher_clause: UnionQueryClause) -> str:
        union_query_string = self.convert_multi_query_clause(s_cypher_clause.multi_query_clauses[0])
        index = 1
        while index < len(s_cypher_clause.multi_query_clauses):
            operator = "UNION"
            if s_cypher_clause.is_all[index - 1]:
                operator = "UNION ALL"
            union_query_string = union_query_string + '\n' + operator + self.convert_multi_query_clause(
                s_cypher_clause.multi_query_clauses[index])
            index = index + 1
        return union_query_string

    def convert_call_clause(self, call_clause: CallClause) -> str:
        pass

    def convert_time_window_limit_clause(self, time_window_limit_clause: TimeWindowLimitClause) -> str:
        pass

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
        with_query_string = with_query_string + self.convert_with_clause(with_query_string.with_clause)
        return with_query_string

    def convert_reading_clause(self, reading_clause: ReadingClause) -> str:
        reading_clause = reading_clause.reading_clause
        if reading_clause.__class__ == MatchClause:
            return self.convert_match_clause(reading_clause)
        elif reading_clause.__class__ == UnwindClause:
            pass
        elif reading_clause.__class__ == CallClause:
            pass

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
                    match_string = match_string + ', '
                if pattern.variable:
                    match_string = match_string + pattern.variable + ' = ' + path_pattern
                else:
                    match_string = match_string + path_pattern
                # 添加节点属性模式的匹配
                for property_pattern in property_patterns:
                    match_string = match_string + ', ' + property_pattern
                interval_conditions.extend(path_interval_conditions)
            elif pattern.__class__ == TemporalPathCall:
                if pattern.start_node.variable is None:
                    pattern.start_node.variable = self.get_random_variable()
                if pattern.edge.variable is None:
                    pattern.edge.variable = self.get_random_variable()
                if pattern.end_node.variable is None:
                    pattern.end_node.variable = self.get_random_variable()
                path_pattern, property_patterns, path_interval_conditions = self.convert_path(
                    pattern.path, match_clause.time_window)
                if call_string != "":
                    call_string = call_string + '\n'
                call_string = call_string + 'MATCH ' + + path_pattern
                # 添加节点属性模式的匹配
                for property_pattern in property_patterns:
                    call_string = call_string + ', ' + property_pattern
                # 添加时态路径的时态条件限制
                if len(path_interval_conditions) != 0:
                    call_string = call_string + '\nWHERE '
                    for index, interval_condition in enumerate(path_interval_conditions):
                        if index == 0:
                            call_string = call_string + interval_condition
                        else:
                            call_string = call_string + ' and ' + interval_condition
                call_string = call_string + '\nCALL ' + pattern.function_name + '( start: ' + pattern.start_node.variable + \
                              ', edge: ' + pattern.edge.variable + ', end: ' + pattern.end_node.variable + \
                              ' )\nYIELD ' + pattern.path.variable
        if call_string != "":
            match_string = call_string + '\n' + match_string
        if match_clause.where_clause or len(interval_conditions) != 0:
            where_string = self.convert_where_clause(match_clause.where_clause, interval_conditions)
            match_string = match_string + '\n' + where_string
        return match_string

    def convert_where_clause(self, where_clause: WhereClause = None, interval_conditions: List[str] = None) -> str:
        if where_clause is None and interval_conditions is None:
            raise ValueError("The where_clause and the interval_conditions can't be None at the same time.")
        if interval_conditions is None:
            interval_conditions = []
        where_string = "WHERE "
        if where_clause:
            expression_string = self.convert_expression(where_clause.expression)
            where_string = where_string + expression_string
        for interval_condition in interval_conditions:
            if where_string != "WHERE ":
                where_string = where_string + ' and '
            where_string = where_string + interval_condition
        return where_string

    def convert_updating_clause(self, updating_clause: UpdatingClause) -> str:
        pass

    def convert_with_clause(self, with_clause: WithClause) -> str:
        pass

    def convert_return_clause(self, return_clause: ReturnClause) -> str:
        return_string = "RETURN "
        for projection_item in return_clause.projection_items:
            if projection_item.is_all:
                for variable in self.variables_dict.keys():
                    if return_string != "RETURN ":
                        return_string = return_string + ', '
                    return_string = return_string + variable
            elif projection_item.expression:
                if return_string != "RETURN ":
                    return_string = return_string + ', '
                return_string = return_string + self.convert_expression(projection_item.expression)
                if projection_item.variable:
                    return_string = return_string + ' AS ' + projection_item.variable
        return return_string

    def convert_unwind_clause(self, unwind_clause: UnwindClause) -> str:
        pass

    def convert_edge(self, edge: SEdge, time_window: TimePoint | Interval = None) -> (str, List[str]):
        # 若边没有变量名，但却有时态限制，那么为它赋一个变量名
        if (edge.interval and edge.variable is None) or time_window:
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
                edge_pattern = edge_pattern + '*' + str(edge.length[0]) + '..' + str(edge.length[1])
        if len(edge.properties) != 0:
            edge_pattern = edge_pattern + '{'
            for index, (key, value) in enumerate(edge.properties.items()):
                if index != 0:
                    edge_pattern = edge_pattern + ', '
                edge_pattern = edge_pattern + key + " : " + str(value)
            edge_pattern = edge_pattern + '}'
        if edge.variable or edge.labels or edge.length[0] != 1 or edge.length[1] != 1 or edge.properties:
            edge_pattern = '-[' + edge_pattern + ']-'
        else:
            edge_pattern = '-' + edge_pattern + '-'
        if edge.direction == edge.LEFT:
            edge_pattern = '<' + edge_pattern
        elif edge.direction == edge.RIGHT:
            edge_pattern = edge_pattern + '>'

        # 边的有效时间限制
        interval_conditions = []
        if edge.interval:
            interval_condition = edge.variable + ".interval_from <= " + str(edge.interval.interval_from.timestamp())
            interval_conditions.append(interval_condition)
            interval_condition = edge.variable + ".interval_to >= " + str(edge.interval.interval_to.timestamp())
            interval_conditions.append(interval_condition)
        if time_window:
            if time_window.__class__ == TimePoint:
                interval_condition = edge.variable + ".interval_from <= " + str(time_window.timestamp())
                interval_conditions.append(interval_condition)
                interval_condition = edge.variable + ".interval_to >= " + str(time_window.timestamp())
                interval_conditions.append(interval_condition)
            else:
                interval_condition = edge.variable + ".interval_from <= " + str(time_window.interval_from.timestamp())
                interval_conditions.append(interval_condition)
                interval_condition = edge.variable + ".interval_to >= " + str(time_window.interval_to.timestamp())
                interval_conditions.append(interval_condition)
        return edge_pattern, interval_conditions

    def convert_node(self, node: SNode, time_window: TimePoint | Interval = None) -> (str, List[str]):
        # 若节点没有变量名，但却有时态限制，那么为它赋一个变量名
        if (node.interval and node.variable is None) or time_window:
            node.variable = self.get_random_variable()
        node_pattern = ""
        if node.variable:
            node_pattern = node.variable
        for label in node.labels:
            node_pattern = node_pattern + ':' + label
        if node.__class__ == PropertyNode:
            node_pattern = node_pattern + "{content: \"" + node.content + "\"}"
        elif node.__class__ == ValueNode:
            node_pattern = node_pattern + "{content: " + self.convert_expression(node.content) + "}"
        node_pattern = '(' + node_pattern + ')'

        # 节点的有效时间限制
        interval_conditions = []
        if node.interval:
            interval_condition = node.variable + ".interval_from <= " + str(node.interval.interval_from.timestamp())
            interval_conditions.append(interval_condition)
            interval_condition = node.variable + ".interval_to >= " + str(node.interval.interval_to.timestamp())
            interval_conditions.append(interval_condition)

        if time_window:
            if time_window.__class__ == TimePoint:
                interval_condition = node.variable + ".interval_from <= " + str(time_window.timestamp())
                interval_conditions.append(interval_condition)
                interval_condition = node.variable + ".interval_to >= " + str(time_window.timestamp())
                interval_conditions.append(interval_condition)
            else:
                interval_condition = node.variable + ".interval_from <= " + str(time_window.interval_from.timestamp())
                interval_conditions.append(interval_condition)
                interval_condition = node.variable + ".interval_to >= " + str(time_window.interval_to.timestamp())
                interval_conditions.append(interval_condition)

        return node_pattern, interval_conditions

    def convert_object_node(self, node: ObjectNode, time_window: TimePoint | Interval = None) -> (
            str, List[str], List[str]):
        # 对象节点模式, 对象节点的有效时间限制
        node_pattern, interval_conditions = self.convert_node(node, time_window)

        # 对象节点属性模式
        property_patterns = []
        for key, value in node.properties.items():
            property_pattern, property_interval_conditions = self.convert_node(key)
            value_pattern, value_interval_conditions = self.convert_node(value)
            property_patterns.append(
                node_pattern + '-[OBJECT_PROPERTY]->' + property_pattern + '-[PROPERTY_VALUE]->' + value_pattern)
            # 属性节点的有效时间限制
            interval_conditions.extend(property_interval_conditions)
            # 值节点的有效时间限制
            interval_conditions.extend(value_interval_conditions)

        return node_pattern, property_patterns, interval_conditions

    def convert_path(self, path: SPath, time_window: TimePoint | Interval = None) -> (str, List[str], List[str]):
        # 路径模式，属性节点和值节点的模式，路径有效时间限制
        path_pattern, property_patterns, interval_conditions = self.convert_object_node(path.nodes[0], time_window)
        index = 1
        while index < len(path.nodes):
            # 生成边模式
            edge_pattern, edge_interval_conditions = self.convert_edge(path.edges[index - 1], time_window)
            path_pattern = path_pattern + edge_pattern
            interval_conditions.extend(edge_interval_conditions)
            # 生成节点模式
            node_pattern, node_property_patterns, node_interval_conditions = self.convert_object_node(path.nodes[index],
                                                                                                      time_window)
            path_pattern = path_pattern + node_pattern
            property_patterns.extend(node_property_patterns)
            interval_conditions.extend(node_interval_conditions)

            index = index + 1
        return path_pattern, property_patterns, interval_conditions

    def convert_expression(self, expression: Expression):
        # 暂用于测试
        if expression.__class__ == str:
            return expression
        return self.convert_or_expression(expression.or_expression)

    def convert_or_expression(self, or_expression: OrExpression):
        expression_string = ""
        for index, xor_expression in enumerate(or_expression.xor_expressions):
            if index != 0:
                expression_string = expression_string + ' OR '
            expression_string = expression_string + self.convert_xor_expression(xor_expression)
        return expression_string

    def convert_xor_expression(self, xor_expression: XorExpression):
        xor_expression_string = ""
        for index, and_expression in enumerate(xor_expression.and_expressions):
            if index != 0:
                xor_expression_string = xor_expression_string + ' XOR '
            xor_expression_string = xor_expression_string + self.convert_and_expression(and_expression)
        return xor_expression_string

    def convert_and_expression(self, and_expression: AndExpression):
        and_expression_string = ""
        for index, not_expression in enumerate(and_expression.not_expressions):
            if index != 0:
                and_expression_string = and_expression_string + ' OR '
            and_expression_string = and_expression_string + self.convert_not_expression(not_expression)
        return and_expression_string

    def convert_not_expression(self, not_expression: NotExpression):
        comparison_string = self.convert_comparison_expression(not_expression.comparison_expression)
        if not_expression.is_not:
            comparison_string = 'NOT ' + comparison_string
        return comparison_string

    def convert_comparison_expression(self, comparison_expression: ComparisonExpression):
        if comparison_expression.comparison_operation and comparison_expression.right_expression:
            return self.convert_subject_expression(
                comparison_expression.left_expression) + ' ' + comparison_expression.comparison_operation + ' ' + self.convert_subject_expression(
                comparison_expression.right_expression)
        return self.convert_subject_expression(comparison_expression.left_expression)

    def convert_subject_expression(self, subject_expression: SubjectExpression):
        subject_string = self.convert_add_subtract_expression(subject_expression.add_or_subtract_expression)
        if subject_expression.predicate_expression:
            predicate_string = ""
            if subject_expression.predicate_expression.__class__ == TimePredicateExpression:
                predicate_string = self.convert_time_predicate_expression(subject_expression.predicate_expression)
            elif subject_expression.predicate_expression.__class__ == StringPredicateExpression:
                predicate_string = self.convert_string_predicate_expression(subject_expression.predicate_expression)
            elif subject_expression.predicate_expression.__class__ == ListPredicateExpression:
                predicate_string = self.convert_list_predicate_expression(subject_expression.predicate_expression)
            return subject_string + ' ' + predicate_string
        return subject_string

    def convert_add_subtract_expression(self, add_subtract_expression: AddSubtractExpression):
        left_string = str(add_subtract_expression.left_expression)
        if add_subtract_expression.add_subtract_operation and add_subtract_expression.right_expression:
            right_string = str(add_subtract_expression.right_expression)
            return left_string + ' ' + add_subtract_expression.add_subtract_operation + ' ' + right_string
        return left_string

    def convert_time_predicate_expression(self, time_predicate_expression: TimePredicateExpression):
        # 待实现
        return time_predicate_expression.time_operation + ' ' + self.convert_add_subtract_expression(
            time_predicate_expression.add_or_subtract_expression)
        pass

    def convert_string_predicate_expression(self, string_predicate_expression: StringPredicateExpression):
        return string_predicate_expression.string_operation + ' ' + self.convert_add_subtract_expression(
            string_predicate_expression.add_or_subtract_expression)

    def convert_list_predicate_expression(self, list_predicate_expression: ListPredicateExpression):
        return 'IN ' + self.convert_add_subtract_expression(list_predicate_expression.add_or_subtract_expression)

    def convert_null_predicate_expression(self, null_predicate_expression: NullPredicateExpression):
        if null_predicate_expression.is_null:
            return 'IS NULL'
        return 'IS NOT NULL'

    def convert_multiply_divide_expression(self, multiply_divide_expression: MultiplyDivideExpression):
        left_string = self.convert_power_expression(multiply_divide_expression.left_expression)
        if multiply_divide_expression.multiply_divide_operation and multiply_divide_expression.right_expression:
            right_string = self.convert_power_expression(multiply_divide_expression.right_expression)
            left_string = left_string + ' ' + multiply_divide_expression.multiply_divide_operation + ' ' + right_string
        return left_string

    def convert_power_expression(self, power_experssion: PowerExpression):
        power_string = ""
        for index, list_expression in enumerate(power_experssion.list_index_expressions):
            if index == 0:
                power_string = self.convert_list_index_expression(list_expression)
            else:
                power_string = power_string + '^' + self.convert_list_index_expression(list_expression) + ''
        return power_string

    def convert_list_index_expression(self, list_index_expression: ListIndexExpression):
        list_index_string = ""
        if list_index_expression.principal_expression.__class__ == PropertiesLabelsExpression:
            list_index_string = self.convert_properties_labels_expressions(
                list_index_expression.principal_expression)
        elif list_index_expression.principal_expression.__class__ == AtTExpression:
            list_index_string = self.convert_at_t_expression(list_index_expression.principal_expression)
        if list_index_expression.index_expression:
            list_index_string = list_index_string + '[' + self.convert_expression(
                list_index_expression.index_expression) + ']'
        if list_index_expression.is_positive is False:
            list_index_string = '-' + list_index_string
        return list_index_string

    def convert_properties_labels_expressions(self, properties_labels_expression: PropertiesLabelsExpression):
        properties_labels_string = self.convert_atom(properties_labels_expression.atom)
        for proprety in properties_labels_expression.property_chains:
            properties_labels_string = properties_labels_string + '.' + proprety
        for label in properties_labels_expression.labels:
            properties_labels_string = properties_labels_string + ':' + label
        return properties_labels_string

    # 待实现
    def convert_at_t_expression(self, at_t_expression: AtTExpression):
        at_t_string = self.convert_atom(at_t_expression.atom)
        for proprety in at_t_expression.property_chains:
            at_t_string = at_t_string + '.' + proprety
        if at_t_expression.is_value:
            at_t_string = at_t_string + '#Value'
        at_t_string = at_t_string + '@T'
        for proprety in at_t_expression.time_property_chains:
            at_t_string = at_t_string + '.' + proprety
        return at_t_string

    def convert_atom(self, atom: Atom) -> str:
        atom = atom.atom
        if atom.__class__ == str:
            return atom
        elif atom.__class__ == ListLiteral:
            return self.convert_list_literal(atom)
        elif atom.__class__ == MapLiteral:
            return self.convert_map_literal(atom)
        elif atom.__class__ == ParenthesizedExpression:
            return self.convert_parenthesized_expression(atom)
        elif atom.__class__ == FunctionInvocation:
            return self.convert_function_invocation(atom)
        else:
            pass

    def convert_list_literal(self, list_literal: ListLiteral):
        list_string = ""
        for index, expression in enumerate(list_literal.expressions):
            if index != 0:
                list_string = list_string + ', '
            list_string = list_string + self.convert_expression(expression)
        list_string = '[' + list_string + ']'
        return list_string

    def convert_map_literal(self, map_literal: MapLiteral):
        map_string = ""
        for index, (key, value) in enumerate(map_literal.keys_values.items()):
            if index != 0:
                map_string = map_string + ', '
            map_string = map_string + key + ': ' + self.convert_expression(value)
        map_string = '{' + map_string + '}'
        return map_string

    def convert_case_expression(self, case_expression: CaseExpression):
        pass

    def convert_list_comprehension(self, list_comprehension: ListComprehension):
        pass

    def convert_pattern_comprehension(self, pattern_comprehension: PatternComprehension):
        pass

    def convert_parenthesized_expression(self, parenthesized_expression: ParenthesizedExpression) -> str:
        return '( ' + self.convert_expression(parenthesized_expression.expression) + ' )'

    def convert_function_invocation(self, function_invocation: FunctionInvocation):
        function_invocation_string = ""
        if function_invocation.is_distinct:
            function_invocation_string = function_invocation_string + 'DISTINCT '
        for index, expression in function_invocation.expressions:
            if index != 0:
                function_invocation_string = function_invocation_string + ','
            function_invocation_string = function_invocation_string + self.convert_expression(expression)
        function_invocation_string = function_invocation.function_name + '( ' + function_invocation_string + ' )'
        return function_invocation_string

    def convert_existential_subquery(self, existential_subquery: ExistentialSubquery):
        pass
