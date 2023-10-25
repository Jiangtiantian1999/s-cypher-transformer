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
        for index, xor_expression in enumerate(or_expression.xor_expressions):
            if index != 0:
                or_expression_string = or_expression_string + " or "
            or_expression_string = or_expression_string + self.convert_xor_expression(xor_expression)
        return or_expression_string

    def convert_xor_expression(self, xor_expression: XorExpression) -> str:
        xor_expression_string = ""
        for index, and_expression in enumerate(xor_expression.and_expressions):
            if index != 0:
                xor_expression_string = xor_expression_string + " xor "
            xor_expression_string = xor_expression_string + self.convert_and_expression(and_expression)
        return xor_expression_string

    def convert_and_expression(self, and_expression: AndExpression) -> str:
        and_expression_string = ""
        for index, not_expression in enumerate(and_expression.not_expressions):
            if index != 0:
                and_expression_string = and_expression_string + " and "
            and_expression_string = and_expression_string + self.convert_not_expression(not_expression)
        return and_expression_string

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
        power_expression_string = self.convert_list_index_expression(power_expression.list_index_expressions[0])
        for index, list_index_expression in enumerate(power_expression.list_index_expressions):
            if index != 0:
                power_expression_string = power_expression_string + '^' + self.convert_list_index_expression(
                    list_index_expression)
        return power_expression_string

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

    def convert_properties_labels_expression(self, properties_labels_expression: PropertiesLabelsExpression) -> str:
        properties_labels_expression_string = self.convert_atom(properties_labels_expression.atom)
        for property_name in properties_labels_expression.property_chains:
            # 是否指定过属性节点
            flag = False
            if properties_labels_expression_string in self.variables_manager.user_object_nodes_dict.keys():
                # 查找对象节点的属性
                object_node = self.variables_manager.user_object_nodes_dict[properties_labels_expression_string]
                for property_node, value_node in object_node.properties:
                    # 所有属性节点都被赋予过变量名（无论是用户赋予的还是系统赋予的）
                    if property_node.variable == property_name:
                        flag = True
                        properties_labels_expression_string = property_node.variable + ".content"
                        break

            if flag is False:
                # 没有指定过属性节点，调用scypher.getPropertyValue，第一个参数为对象节点，第二个参数为属性名
                # 不确定是否查找对象节点的属性，也可能是查找Map类型数据的键值，scypher.getPropertyValue能够自动识别
                properties_labels_expression_string = "scypher.getPropertyValue(" + properties_labels_expression_string + ", \"" + property_name + "\")"
                if self.clause_converter.current_clause in ["WITH", "RETURN"]:
                    unwind_variable = self.variables_manager.get_random_variable()
                    self.clause_converter.unwind_variables_dict[properties_labels_expression_string] = unwind_variable
                    properties_labels_expression_string = unwind_variable
        for label in properties_labels_expression.labels:
            # 判断某节点/边是否有某（些）标签
            properties_labels_expression_string = properties_labels_expression_string + ':' + label
        return properties_labels_expression_string

    def convert_at_t_expression(self, at_t_expression: AtTExpression) -> str:
        at_t_expression_string = self.convert_atom(at_t_expression.atom)
        object_variable, property_name = at_t_expression_string, None
        for property in at_t_expression.property_chains:
            object_variable, property_name = at_t_expression_string, property
            at_t_expression_string = at_t_expression_string + '.' + property

        if property_name is None:
            # 返回对象节点或边的有效时间
            at_t_expression_string = "scypher.interval(" + object_variable + ".intervalFrom, " + object_variable + ".intervalTo)"
        else:
            # 返回属性节点/值节点的有效时间

            # 是否指定过属性节点
            flag = False
            if object_variable in self.variables_manager.user_object_nodes_dict.keys():
                object_node = self.variables_manager.user_object_nodes_dict[object_variable]
                for property_node, value_node in object_node.properties.items():
                    if property_node.content == property_name:
                        # 指定过属性节点，必然也指定过值节点，且所有属性节点和值节点都被赋予过变量名（无论是用户赋予的还是系统赋予的），
                        flag = True
                        if at_t_expression.is_value is None:
                            # 返回属性节点的有效时间
                            at_t_expression_string = property_node.variable + ".content"
                        else:
                            # 返回值节点的有效时间
                            at_t_expression_string = value_node.variable + ".content"
                    break
            if flag is False:
                # 没有指定过属性节点
                if at_t_expression.is_value is None:
                    # 返回属性节点的有效时间，调用scypher.getPropertyInterval，第一个参数为对象节点，第二个参数为属性名
                    at_t_expression_string = "scypher.getPropertyInterval(" + object_variable + ", \"" + property_name + "\")"
                else:
                    # 返回值节点的有效时间，调用scypher.getValueInterval，第一个参数为对象节点，第二个参数为属性名
                    at_t_expression_string = "scypher.getPropertyInterval(" + object_variable + ", \"" + property_name + "\")"

                if self.clause_converter.current_clause in ["WITH", "RETURN"]:
                    unwind_variable = self.variables_manager.get_random_variable()
                    self.clause_converter.unwind_variables_dict[at_t_expression_string] = unwind_variable
                    at_t_expression_string = unwind_variable

        for index, time_property in enumerate(at_t_expression.time_property_chains):
            if index == 0 and (property_name is None or flag is True):
                if time_property == "from":
                    at_t_expression_string = object_variable + ".intervalFrom"
                elif time_property == "to":
                    at_t_expression_string = object_variable + ".intervalTo"
            else:
                at_t_expression_string = at_t_expression_string + '.' + time_property

        return at_t_expression_string

    def convert_atom(self, atom: Atom) -> str:
        atom = atom.atom
        if atom.__class__ == str:
            return self.convert_literal(atom)
        elif atom.__class__ == ListLiteral:
            return self.convert_list_literal(atom)
        elif atom.__class__ == MapLiteral:
            return self.convert_map_literal(atom)
        elif atom.__class__ == CaseExpression:
            pass
        elif atom.__class__ == ListComprehension:
            pass
        elif atom.__class__ == PatternComprehension:
            pass
        elif atom.__class__ == Quantifier:
            pass
        elif atom.__class__ == PatternPredicate:
            pass
        elif atom.__class__ == ParenthesizedExpression:
            return '(' + self.convert_expression(atom.expression) + ')'
        elif atom.__class__ == FunctionInvocation:
            return self.convert_function_invocation(atom)
        elif atom.__class__ == ExistentialSubquery:
            pass

    def convert_literal(self, literal: str) -> str:
        if literal.upper() == "NOW" and literal not in self.variables_manager.user_variables:
            return "\"" + literal + "\""
        # property属性类型，包括数值类，字符类，布尔类，空间类和时间类（时间点和时间段）
        return literal

    def convert_list_literal(self, list_literal: ListLiteral) -> str:
        list_literal_string = ""
        for index, expression in enumerate(list_literal.expressions):
            if index != 0:
                list_literal_string = list_literal_string + ", "
            list_literal_string = list_literal_string + self.convert_expression(expression)
        return '[' + list_literal_string + ']'

    def convert_map_literal(self, map_literal: MapLiteral) -> str:
        map_literal_string = ""
        for index, (key, value) in enumerate(map_literal.keys_values.items()):
            if index != 0:
                map_literal_string = map_literal_string + ", "
            map_literal_string = map_literal_string + key + ": " + self.convert_expression(value)
        return '{' + map_literal_string + '}'

    def convert_function_invocation(self, function_invocation: FunctionInvocation) -> str:
        function_invocation_string = ""
        if function_invocation.is_distinct:
            function_invocation_string = "DISTINCT "
        for index, expression in enumerate(function_invocation.expressions):
            if index != 0:
                function_invocation_string = function_invocation_string + ", "
            function_invocation_string = function_invocation_string + self.convert_expression(expression)
        if function_invocation.function_name in ConfigReader.config["SCYPHER"]["FUNCTION_NAME"]:
            function_invocation_string = "scypher." + function_invocation.function_name + '(' + function_invocation_string + ')'
        else:
            function_invocation_string = function_invocation.function_name + '(' + function_invocation_string + ')'
        return function_invocation_string
