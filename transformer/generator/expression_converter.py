from transformer.conf.config_reader import ConfigReader
from transformer.ir.s_expression import *
from transformer.ir.s_graph import *


class ExpressionConverter:
    def __init__(self):
        self.variables_manager = None
        self.graph_converter = None
        self.clause_converter = None

    def convert_expression(self, expression: Expression) -> str:
        return self.convert_or_expression(expression.or_expression)

    def convert_or_expression(self, or_expression: OrExpression) -> str:
        or_expression_string = ""
        for xor_expression in or_expression.xor_expressions:
            or_expression_string = or_expression_string + self.convert_xor_expression(xor_expression) + " or "
        return or_expression_string.rstrip(" or ")

    def convert_xor_expression(self, xor_expression: XorExpression) -> str:
        xor_expression_string = ""
        for and_expression in xor_expression.and_expressions:
            xor_expression_string = xor_expression_string + self.convert_and_expression(and_expression) + " xor "
        return xor_expression_string.rstrip(" xor ")

    def convert_and_expression(self, and_expression: AndExpression) -> str:
        and_expression_string = ""
        for not_expression in and_expression.not_expressions:
            and_expression_string = and_expression_string + self.convert_not_expression(not_expression) + " and "
        return and_expression_string.rstrip(" and ")

    def convert_not_expression(self, not_expression: NotExpression) -> str:
        comparison_expression_string = self.convert_comparison_expression(not_expression.comparison_expression)
        if not_expression.is_not:
            comparison_expression_string = "not " + comparison_expression_string
        return comparison_expression_string

    def convert_comparison_expression(self, comparison_expression: ComparisonExpression) -> str:
        comparison_expression_string = self.convert_subject_expression(comparison_expression.subject_expressions[0])
        for index, comparison_operation in enumerate(comparison_expression.comparison_operations):
            comparison_expression_string = comparison_expression_string + ' ' + comparison_operation + ' ' + self.convert_subject_expression(
                comparison_expression.subject_expressions[index + 1])
        return comparison_expression_string

    def convert_subject_expression(self, subject_expression: SubjectExpression) -> str:
        subject_expression_string = self.convert_add_subtract_expression(subject_expression.add_or_subtract_expression)
        predicate_expression = subject_expression.predicate_expression
        if predicate_expression:
            if predicate_expression.__class__ == TimePredicateExpression:
                predicate_expression_string = self.convert_add_subtract_expression(
                    predicate_expression.add_subtract_expression)
                subject_expression_string = "scypher." + predicate_expression.time_operation.lower() + '(' + subject_expression_string + ", " + predicate_expression_string + ')'
            elif predicate_expression.__class__ == StringPredicateExpression:
                predicate_expression_string = self.convert_add_subtract_expression(
                    predicate_expression.add_subtract_expression)
                subject_expression_string = subject_expression_string + ' ' + predicate_expression.string_operation + ' ' + predicate_expression_string
            elif predicate_expression.__class__ == ListPredicateExpression:
                predicate_expression_string = self.convert_add_subtract_expression(
                    predicate_expression.add_subtract_expression)
                subject_expression_string = subject_expression_string + ' IN ' + predicate_expression_string
            elif predicate_expression.__class__ == NullPredicateExpression:
                if predicate_expression.is_null:
                    subject_expression_string = subject_expression_string + " IS NULL"
                else:
                    subject_expression_string = subject_expression_string + " IS NOT NULL"
        return subject_expression_string

    def convert_add_subtract_expression(self, add_subtract_expression: AddSubtractExpression) -> str:
        add_subtract_expression_string = self.convert_multiply_divide_expression(
            add_subtract_expression.multiply_divide_expressions[0])

        for index, add_subtract_operation in enumerate(add_subtract_expression.add_subtract_operations):
            add_subtract_expression_string = add_subtract_expression_string + ' ' + add_subtract_operation + ' ' + self.convert_multiply_divide_expression(
                add_subtract_expression.multiply_divide_expressions[index + 1])

        return add_subtract_expression_string

    def convert_multiply_divide_expression(self, multiply_divide_expression: MultiplyDivideExpression) -> str:
        multiply_divide_expression_string = self.convert_power_expression(
            multiply_divide_expression.power_expressions[0])

        for index, multiply_divide_operation in enumerate(multiply_divide_expression.multiply_divide_operations):
            multiply_divide_expression_string = multiply_divide_expression_string + ' ' + multiply_divide_operation + ' ' + self.convert_power_expression(
                multiply_divide_expression.power_expressions[index + 1])
        return multiply_divide_expression_string

    def convert_power_expression(self, power_expression: PowerExpression) -> str:
        power_expression_string = ""
        for list_index_expression in power_expression.list_index_expressions:
            power_expression_string = power_expression_string + '^' + self.convert_list_index_expression(
                list_index_expression)
        return power_expression_string.lstrip('^')

    def convert_list_index_expression(self, list_index_expression: ListIndexExpression) -> str:
        list_index_expression_string = ""
        if list_index_expression.principal_expression.__class__ == PropertiesLabelsExpression:
            list_index_expression_string = self.convert_properties_labels_expression(
                list_index_expression.principal_expression)
        elif list_index_expression.principal_expression.__class__ == AtTExpression:
            list_index_expression_string = self.convert_at_t_expression(list_index_expression.principal_expression)

        for index_expression in list_index_expression.index_expressions:
            left_expression_string = self.convert_expression(index_expression.left_expression)
            if index_expression.right_expression is None:
                list_index_expression_string = list_index_expression_string + '[' + left_expression_string + ']'
            else:
                right_expression_string = self.convert_expression(index_expression.right_expression)
                list_index_expression_string = list_index_expression_string + '[' + left_expression_string + ".." + right_expression_string + ']'

        if list_index_expression.is_positive is False:
            list_index_expression_string = '-' + list_index_expression_string

        return list_index_expression_string

    def get_property_value(self, variable_name, property_name):
        if variable_name in self.variables_manager.user_object_nodes_dict.keys():
            # 查找对象节点的属性
            object_node = self.variables_manager.user_object_nodes_dict[variable_name]
            for property_node, value_node in object_node.properties.items():
                # 所有属性节点和值节点都被赋予过变量名（无论是用户赋予的还是系统赋予的）
                if property_node.variable == property_name:
                    if variable_name in self.variables_manager.updating_object_nodes_dict.keys():
                        # 查找在更新语句中定义的对象节点的属性
                        return self.convert_expression(value_node.content)
                    else:
                        return value_node.variable + ".content"
            if variable_name in self.variables_manager.updating_object_nodes_dict.keys():
                raise ValueError('\'' + variable_name + "' doesn't have property '" + property_name + '\'')
        elif variable_name in self.variables_manager.user_edges_dict.keys():
            # 查找边的属性
            if variable_name in self.variables_manager.updating_edges_dict.keys():
                # 查找在更新语句中定义的边的属性
                edge = self.variables_manager.updating_edges_dict[variable_name]
                return self.convert_expression(edge.properties[property_name])
            else:
                return variable_name + '.' + property_name
        elif variable_name in self.variables_manager.user_paths_dict.keys():
            # 查找路径的属性，但实际上路径没有属性，报错
            raise ValueError("Paths have no properties.")
        # 没有指定过属性节点，调用scypher.getPropertyValue，第一个参数为对象节点，第二个参数为属性名
        # 不确定是查找对象节点的属性，还是查找Map, Point, Duration, Date, Time, LocalTime, LocalDateTime or DateTime的属性，scypher.getPropertyValue函数内部应该加以区分
        unwind_variable = self.variables_manager.get_random_variable()
        self.clause_converter.unwind_clause_dict[
            unwind_variable] = "scypher.getPropertyValue(" + variable_name + ", \"" + property_name + "\")"
        return unwind_variable

    def convert_properties_labels_expression(self, properties_labels_expression: PropertiesLabelsExpression) -> str:
        properties_labels_expression_string = self.convert_atom(properties_labels_expression.atom)
        for property_name in properties_labels_expression.property_chains:
            properties_labels_expression_string = self.get_property_value(properties_labels_expression_string,
                                                                          property_name)

        for label in properties_labels_expression.labels:
            # 判断某节点/边是否有某（些）标签
            properties_labels_expression_string = properties_labels_expression_string + ':' + label
        return properties_labels_expression_string

    def convert_at_t_expression(self, at_t_expression: AtTExpression) -> str:
        at_t_expression_string = self.convert_atom(at_t_expression.atom)
        for index, property_name in enumerate(at_t_expression.property_chains):
            if index != len(at_t_expression.property_chains) - 1:
                at_t_expression_string = self.get_property_value(at_t_expression, property_name)

        element_variable = at_t_expression_string
        interval_from, interval_to = None, None
        # 是否指定过访问的对象节点/属性节点/值节点
        flag = False
        if len(at_t_expression.property_chains) == 0:
            # 返回对象节点或边的有效时间
            flag = True
            if element_variable in self.variables_manager.updating_object_nodes_dict.keys():
                # 查找在更新语句中定义的对象节点的有效时间
                updating_object_node = self.variables_manager.updating_object_nodes_dict[element_variable]
                if updating_object_node.interval:
                    interval_from = self.graph_converter.convert_time_point_literal(
                        updating_object_node.interval.interval_from)
                    interval_to = self.graph_converter.convert_time_point_literal(
                        updating_object_node.interval.interval_to)
                else:
                    interval_from = "scypher.timePoint()"
                    interval_to = "scypher.timePoint(\"NOW\")"
                at_t_expression_string = "scypher.interval(" + interval_from + ", " + interval_to + ')'
            else:
                at_t_expression_string = "scypher.interval(" + element_variable + ".intervalFrom, " + element_variable + ".intervalTo)"
        else:
            # 返回属性节点/值节点的有效时间
            property_name = at_t_expression.property_chains[-1]
            if element_variable in self.variables_manager.user_object_nodes_dict.keys():
                object_node = self.variables_manager.user_object_node_dict[element_variable]
                for property_node, value_node in object_node.properties.items():
                    if property_node.content == property_name:
                        # 指定过属性节点，必然也指定过值节点，且所有属性节点和值节点都被赋予过变量名（无论是用户赋予的还是系统赋予的）
                        flag = True
                        if element_variable in self.variables_manager.updating_object_nodes_dict.keys():
                            # 查找在更新语句中定义的属性节点/值节点的有效时间
                            if at_t_expression.is_value is None:
                                # 返回属性节点的有效时间
                                interval_from = self.graph_converter.convert_time_point_literal(
                                    property_node.interval.interval_from)
                                interval_to = self.graph_converter.convert_time_point_literal(
                                    property_node.interval.interval_to)
                            else:
                                # 返回值节点的有效时间
                                interval_from = self.graph_converter.convert_time_point_literal(
                                    property_node.interval.interval_from)
                                interval_to = self.graph_converter.convert_time_point_literal(
                                    property_node.interval.interval_to)
                            at_t_expression_string = "scypher.interval(" + interval_from + ", " + interval_to + ')'
                        else:
                            if at_t_expression.is_value is None:
                                # 返回属性节点的有效时间
                                element_variable = property_node.variable
                            else:
                                # 返回值节点的有效时间
                                element_variable = value_node.variable
                            at_t_expression_string = "scypher.interval(" + element_variable + ".intervalFrom, " + element_variable + ".intervalTo)"
                    break
                if element_variable in self.variables_manager.updating_object_nodes_dict.keys() and flag is False:
                    raise ValueError('\'' + element_variable + "' doesn't have property '" + property_name + '\'')
            elif element_variable in list(self.variables_manager.user_edges_dict.keys()) + list(self.variables_manager.user_paths_dict.keys()):
                # 边/路径的属性没有有效时间（实际上路径没有属性）
                raise ValueError(
                    "Only the property of node has a effective time. '" + element_variable + "' is not a node.")
            if flag is False:
                if at_t_expression.is_value is None:
                    # 返回属性节点的有效时间，调用scypher.getPropertyInterval，第一个参数为对象节点，第二个参数为属性名
                    # 实际上object_variable.property_name也可能为对象节点，scypher.getPropertyInterval函数内部应该加以区分
                    at_t_expression_string = "scypher.getPropertyInterval(" + element_variable + ", \"" + property_name + "\")"
                else:
                    # 返回值节点的有效时间，调用scypher.getValueInterval，第一个参数为对象节点，第二个参数为属性名
                    at_t_expression_string = "scypher.getValueInterval(" + element_variable + ", \"" + property_name + "\")"
                    # 只有返回值节点的有效时间时可能返回多个值
                    unwind_variable = self.variables_manager.get_random_variable()
                    self.clause_converter.unwind_clause_dict[unwind_variable] = at_t_expression_string
                    at_t_expression_string = unwind_variable

        for index, time_property in enumerate(at_t_expression.time_property_chains):
            if index == 0 and flag is True:
                if time_property == "from":
                    if interval_from is None:
                        at_t_expression_string = element_variable + ".intervalFrom"
                    else:
                        at_t_expression_string = "scypher.timePoint(" + interval_from + ")"
                elif time_property == "to":
                    if interval_to is None:
                        at_t_expression_string = element_variable + ".intervalTo"
                    else:
                        at_t_expression_string = "scypher.timePoint(" + interval_to + ")"
                else:
                    raise ValueError("Interval does not have property '" + time_property + "'")
            else:
                at_t_expression_string = at_t_expression_string + '.' + time_property

        return at_t_expression_string

    def convert_atom(self, atom: Atom) -> str:
        particle = atom.particle
        if particle.__class__ == str:
            if particle.upper() == "NOW" and particle not in self.variables_manager.user_variables:
                return '\"' + particle + '\"'
            return particle
        elif particle.__class__ == ListLiteral:
            return self.convert_list_literal(particle)
        elif particle.__class__ == MapLiteral:
            return self.convert_map_literal(particle)
        elif particle.__class__ == CaseExpression:
            pass
        elif particle.__class__ == ListComprehension:
            pass
        elif particle.__class__ == PatternComprehension:
            pass
        elif particle.__class__ == Quantifier:
            pass
        elif particle.__class__ == PatternPredicate:
            pass
        elif particle.__class__ == ParenthesizedExpression:
            return '(' + self.convert_expression(particle.expression) + ')'
        elif particle.__class__ == FunctionInvocation:
            return self.convert_function_invocation(particle)
        elif particle.__class__ == ExistentialSubquery:
            pass

    def convert_list_literal(self, list_literal: ListLiteral) -> str:
        list_literal_string = ""
        for expression in list_literal.expressions:
            list_literal_string = list_literal_string + self.convert_expression(expression) + ", "
        return '[' + list_literal_string.rstrip(", ") + ']'

    def convert_map_literal(self, map_literal: MapLiteral) -> str:
        map_literal_string = ""
        for key, value in map_literal.keys_values.items():
            map_literal_string = map_literal_string + key + ": " + self.convert_expression(value) + ", "
        return '{' + map_literal_string.rstrip(", ") + '}'

    def convert_function_invocation(self, function_invocation: FunctionInvocation) -> str:
        function_invocation_string = ""
        if function_invocation.is_distinct:
            function_invocation_string = "DISTINCT "
        for expression in function_invocation.expressions:
            function_invocation_string = function_invocation_string + self.convert_expression(expression) + ", "
        function_invocation_string = function_invocation_string.rstrip(", ")

        if function_invocation.function_name in ConfigReader.config["SCYPHER"]["FUNCTION_NAME"]:
            function_invocation_string = "scypher." + function_invocation.function_name + '(' + function_invocation_string + ')'
        else:
            function_invocation_string = function_invocation.function_name + '(' + function_invocation_string + ')'
        return function_invocation_string
