import re

from transformer.ir.s_expression import *
from transformer.ir.s_graph import ObjectNode, ValueNode, PropertyNode


class ExpressionConverter:
    # 注意：该类中的所有variables_manager均为VariablesManager类型，由于与VariablesManager相互引用，故此处不写明类型。
    @staticmethod
    def convert_expression(expression: Expression, variables_manager) -> (str,):
        return ExpressionConverter.convert_or_expression(expression.or_expression, variables_manager)

    @staticmethod
    def convert_or_expression(or_expression: OrExpression, variables_manager) -> (str,):
        or_expression_string, or_expression_type = "", None
        for index, xor_expression in enumerate(or_expression.xor_expressions):
            xor_expression_string, xor_expression_type = ExpressionConverter.convert_xor_expression(xor_expression,
                                                                                                    variables_manager)
            if index != 0:
                or_expression_string = or_expression_string + " or "
            else:
                or_expression_type = xor_expression_type
            or_expression_string = or_expression_string + xor_expression_string
        return or_expression_string, or_expression_type

    @staticmethod
    def convert_xor_expression(xor_expression: XorExpression, variables_manager) -> (str,):
        xor_expression_string, xor_expression_type = "", None
        for index, and_expression in enumerate(xor_expression.and_expressions):
            and_expression_string, and_expression_type = ExpressionConverter.convert_and_expression(and_expression,
                                                                                                    variables_manager)
            if index != 0:
                xor_expression_string = xor_expression_string + " xor "
            else:
                xor_expression_type = and_expression_type
            xor_expression_string = xor_expression_string + and_expression_string
        return xor_expression_string, xor_expression_type

    @staticmethod
    def convert_and_expression(and_expression: AndExpression, variables_manager) -> (str,):
        and_expression_string, and_expression_type = "", None
        for index, not_expression in enumerate(and_expression.not_expressions):
            not_expression_string, not_expression_type = ExpressionConverter.convert_not_expression(not_expression,
                                                                                                    variables_manager)
            if index != 0:
                and_expression_string = and_expression_string + " and "
            else:
                and_expression_type = not_expression_type
            and_expression_string = and_expression_string + not_expression_string
        return and_expression_string, and_expression_type

    @staticmethod
    def convert_not_expression(not_expression: NotExpression, variables_manager) -> (str,):
        comparison_expression_string, comparison_expression_type = ExpressionConverter.convert_comparison_expression(
            not_expression.comparison_expression, variables_manager)
        if not_expression.is_not:
            comparison_expression_string = "not " + comparison_expression_string
        return comparison_expression_string, comparison_expression_type

    @staticmethod
    def convert_comparison_expression(comparison_expression: ComparisonExpression, variables_manager) -> (str,):
        comparison_expression_string, comparison_expression_type = ExpressionConverter.convert_subject_expression(
            comparison_expression.subject_expressions[0], variables_manager)
        for index, comparison_operation in enumerate(comparison_expression.comparison_operations):
            comparison_expression_type = "property"
            subject_expression_string, subject_expression_type = ExpressionConverter.convert_subject_expression(
                comparison_expression.subject_expressions[index + 1], variables_manager)
            comparison_expression_string = comparison_expression_string + ' ' + comparison_operation + ' ' + subject_expression_string
        return comparison_expression_string, comparison_expression_type

    @staticmethod
    def convert_subject_expression(subject_expression: SubjectExpression, variables_manager) -> (str,):
        subject_expression_string, subject_expression_type = ExpressionConverter.convert_add_subtract_expression(
            subject_expression.add_or_subtract_expression, variables_manager)
        predicate_expression = subject_expression.predicate_expression
        if predicate_expression:
            subject_expression_type = "property"
            if predicate_expression.__class__ == TimePredicateExpression:
                predicate_expression_string, predicate_expression_type = ExpressionConverter.convert_add_subtract_expression(
                    predicate_expression.add_subtract_expression, variables_manager)
                subject_expression_string = "scypher." + predicate_expression.time_operation.lower() + '(' + subject_expression_string + ", " + predicate_expression_string + ')'
            elif predicate_expression.__class__ == StringPredicateExpression:
                predicate_expression_string, predicate_expression_type = ExpressionConverter.convert_add_subtract_expression(
                    predicate_expression.add_subtract_expression, variables_manager)
                subject_expression_string = subject_expression_string + ' ' + predicate_expression.string_operation + ' ' + predicate_expression_string
            elif predicate_expression.__class__ == ListPredicateExpression:
                predicate_expression_string, predicate_expression_type = ExpressionConverter.convert_add_subtract_expression(
                    predicate_expression.add_subtract_expression, variables_manager)
                subject_expression_string = subject_expression_string + ' IN ' + predicate_expression_string, "property"
            elif predicate_expression.__class__ == NullPredicateExpression:
                if predicate_expression.is_null:
                    subject_expression_string = subject_expression_string + " IS NULL", "property"
                else:
                    subject_expression_string = subject_expression_string + " IS NOT NULL", "property"
        return subject_expression_string, subject_expression_type

    @staticmethod
    def convert_add_subtract_expression(add_subtract_expression: AddSubtractExpression, variables_manager) -> (str,):
        add_subtract_expression_string, add_or_subtract_expression_type = ExpressionConverter.convert_multiply_divide_expression(
            add_subtract_expression.multiply_divide_expressions[0], variables_manager)
        multiply_divide_expression_types, list_flag = [], False
        for index, add_subtract_operation in enumerate(add_subtract_expression.add_subtract_operations):
            multiply_divide_expression_string, multiply_divide_expression_type = ExpressionConverter.convert_multiply_divide_expression(
                add_subtract_expression.multiply_divide_expressions[index + 1], variables_manager)
            multiply_divide_expression_types.extend(multiply_divide_expression_type)
            if multiply_divide_expression_type.__class__ == list:
                # List与其他元素相加，结果也为List
                list_flag = True
            add_subtract_expression_string = add_subtract_expression_string + ' ' + add_subtract_operation + ' ' + multiply_divide_expression_string
        if list_flag:
            add_or_subtract_expression_type = multiply_divide_expression_types
        return add_subtract_expression_string, add_or_subtract_expression_type

    @staticmethod
    def convert_multiply_divide_expression(multiply_divide_expression: MultiplyDivideExpression, variables_manager) -> (
            str,):
        multiply_divide_expression_string, multiply_divide_expression_type = ExpressionConverter.convert_power_expression(
            multiply_divide_expression.power_expressions[0], variables_manager)
        for index, multiply_divide_operation in enumerate(multiply_divide_expression.multiply_divide_operations):
            power_expression_string, power_expression_type = ExpressionConverter.convert_power_expression(
                multiply_divide_expression.power_expressions[index + 1], variables_manager)
            multiply_divide_expression_string = multiply_divide_expression_string + ' ' + multiply_divide_operation + ' ' + power_expression_string
        return multiply_divide_expression_string, multiply_divide_expression_type

    @staticmethod
    def convert_power_expression(power_expression: PowerExpression, variables_manager) -> (str,):
        power_expression_string, power_expression_type = ExpressionConverter.convert_list_index_expression(
            power_expression.list_index_expressions[0], variables_manager)
        for index, list_index_expression in enumerate(power_expression.list_index_expressions):
            if index != 0:
                list_index_expression_string, list_index_expression_type = ExpressionConverter.convert_list_index_expression(
                    list_index_expression, variables_manager)
                power_expression_string = power_expression_string + '^' + list_index_expression_string
        return power_expression_string, power_expression_type

    @staticmethod
    def convert_list_index_expression(list_index_expression: ListIndexExpression, variables_manager) -> (str,):
        list_index_expression_string, list_index_expression_type = "", None
        if list_index_expression.principal_expression.__class__ == PropertiesLabelsExpression:
            list_index_expression_string, list_index_expression_type = ExpressionConverter.convert_properties_labels_expression(
                list_index_expression.principal_expression, variables_manager)
        elif list_index_expression.principal_expression.__class__ == AtTExpression:
            list_index_expression_string, list_index_expression_type = ExpressionConverter.convert_at_t_expression(
                list_index_expression.principal_expression, variables_manager)

        for index_expression in list_index_expression.index_expressions:
            left_expression_string, left_expression_type = ExpressionConverter.convert_expression(
                index_expression.left_expression, variables_manager)
            if index_expression.right_expression is None:
                list_index_expression_string = list_index_expression_string + '[' + left_expression_string + ']'
                if list_index_expression_type.__class__ == list:
                    list_index_expression_type = list_index_expression_type[int(left_expression_string)]
            else:
                right_expression_string, right_expression_type = ExpressionConverter.convert_expression(
                    index_expression.right_expression, variables_manager)
                list_index_expression_string = list_index_expression_string + '[' + left_expression_string + ".." + right_expression_string + ']'
                if list_index_expression_type.__class__ == list:
                    list_index_expression_type = list_index_expression_type[
                                                 int(left_expression_string):int(right_expression_string)]

        if list_index_expression.is_positive is False:
            list_index_expression_string = '-' + list_index_expression_string
        return list_index_expression_string, list_index_expression_type

    @staticmethod
    def convert_properties_labels_expression(properties_labels_expression: PropertiesLabelsExpression,
                                             variables_manager) -> (str,):
        properties_labels_expression_string, properties_labels_expression_type = ExpressionConverter.convert_atom(
            properties_labels_expression.atom, variables_manager)
        for property in properties_labels_expression.property_chains:
            if properties_labels_expression_type.__class__ == ObjectNode or properties_labels_expression_type == "node":
                value_node_variable = None
                if properties_labels_expression_type.__class__ == ObjectNode:
                    for property_node, value_node in properties_labels_expression_type.properties.items():
                        if property_node.content == property:
                            if value_node.variable in variables_manager.variables_dict.keys():
                                value_node_variable = value_node.variable
                            break
                if value_node_variable is None:
                    value_node_variable = variables_manager.get_random_variable()
                    if properties_labels_expression_string in variables_manager.variables_dict.keys():
                        # 不需要为对象节点命名
                        object_node_variable = properties_labels_expression_string
                    else:
                        object_node_variable = variables_manager.get_random_variable()
                        variables_manager.variables_dict[object_node_variable] = ObjectNode(
                            variable=object_node_variable)
                        with_project_item = properties_labels_expression_string + " as " + object_node_variable
                        variables_manager.with_project_items.append(with_project_item)

                    property_pattern = '(' + object_node_variable + ":Object)-[:OBJECT_PROPERTY]->(:Property{content:\"" + property + "\"})-[:PROPERTY_VALUE]->(" + value_node_variable + ":Value)"
                    variables_manager.property_patterns.append(property_pattern)
                    variables_manager.variables_dict[value_node_variable] = ValueNode(None, value_node_variable)
                    if properties_labels_expression_type.__class__ == ObjectNode:
                        properties_labels_expression_type.properties[PropertyNode(property)] = \
                            variables_manager.variables_dict[value_node_variable]
                    else:
                        variables_manager.variables_dict[object_node_variable] = ObjectNode(
                            variable=object_node_variable,
                            properties={PropertyNode(property): variables_manager.variables_dict[value_node_variable]})

                # Property values can only be of primitive types or arrays thereof.
                # 意味着不会产生嵌套访问对象节点的属性，因此将list记为property也不会产生影响
                properties_labels_expression_string = value_node_variable + ".content"
                properties_labels_expression_type = "property"
            else:
                if properties_labels_expression_type.__class__ == dict:
                    properties_labels_expression_type = properties_labels_expression_type[property]
                # 查找节点/边的属性
                properties_labels_expression_string = properties_labels_expression_string + '.' + property
        for label in properties_labels_expression.labels:
            # 判断某节点/边是否有某（些）标签
            properties_labels_expression_string = properties_labels_expression_string + ':' + label
            properties_labels_expression_type = "property"
        return properties_labels_expression_string, properties_labels_expression_type

    @staticmethod
    def convert_at_t_expression(at_t_expression: AtTExpression, variables_manager) -> (str,):
        at_t_expression_string, at_t_expression_type = ExpressionConverter.convert_atom(at_t_expression.atom,
                                                                                        variables_manager)
        object_variable, property_name = at_t_expression_string, None
        for property in at_t_expression.property_chains:
            object_variable, property_name = at_t_expression_string, property
            at_t_expression_string = at_t_expression_string + '.' + property

        if object_variable in variables_manager.variables_dict.keys():
            # 不需要为对象节点命名
            object_node_variable = object_variable
        else:
            object_node_variable = variables_manager.get_random_variable()
            with_project_item = object_variable + " as " + object_node_variable
            variables_manager.with_project_items.append(with_project_item)
            variables_manager.variables_dict[object_node_variable] = ObjectNode(variable=object_node_variable)

        # 所查找的对象节点/属性节点/值节点的变量名
        interval_variable = object_variable

        if property_name is None:
            # 返回对象节点的有效时间
            at_t_expression_string = "{from: " + object_node_variable + ".intervalFrom, to: " + object_node_variable + ".intervalTo}"
            interval_variable = object_node_variable
        elif property_name is not None and at_t_expression.is_value is False:
            # 返回属性节点的有效时间
            property_node_variable = None
            if variables_manager.variables_dict[object_node_variable].__class__ == ObjectNode:
                for property_node, value_node in variables_manager.variables_dict[
                    object_node_variable].properties.items():
                    if property_node.content == property_name:
                        if property_node.variable in variables_manager.variables_dict.keys():
                            property_node_variable = property_node.variable
                        break
            if property_node_variable is None:
                property_node_variable = variables_manager.get_random_variable()
                property_pattern = '(' + object_node_variable + ":Object)-[:OBJECT_PROPERTY]->(" + property_node_variable + ":Property{content:\"" + property_name + "\"})"
                variables_manager.property_patterns.append(property_pattern)
                variables_manager.variables_dict[property_node_variable] = PropertyNode(property_name,
                                                                                        property_node_variable)
                if variables_manager.variables_dict[object_node_variable].__class__ == ObjectNode:
                    variables_manager.variables_dict[object_node_variable].properties[
                        variables_manager.variables_dict[property_node_variable]] = None
                else:
                    variables_manager.variables_dict[object_node_variable] = ObjectNode(
                        variable=object_node_variable,
                        properties={variables_manager.variables_dict[property_node_variable]: None})
            at_t_expression_string = "{from: " + property_node_variable + ".intervalFrom, to: " + property_node_variable + ".intervalTo}"
            interval_variable = property_node_variable
        elif property_name is not None and at_t_expression.is_value:
            # 返回值节点的有效时间
            value_node_variable = None
            if variables_manager.variables_dict[object_variable].__class__ == ObjectNode:
                for property_node, value_node in variables_manager.variables_dict[object_variable]:
                    if property_node.content == property_name:
                        if value_node.variable in variables_manager.variables_dict.keys():
                            value_node_variable = value_node.variable
                        break
            if value_node_variable is None:
                value_node_variable = variables_manager.get_random_variable()
                property_pattern = '(' + object_node_variable + ":Object)-[:OBJECT_PROPERTY]->(:Property{content:\"" + property_name + "\"})-[:PROPERTY_VALUE]->(" + value_node_variable + ":Value)"
                variables_manager.property_patterns.append(property_pattern)
                variables_manager.variables_dict[value_node_variable] = ValueNode(None, value_node_variable)
                if variables_manager.variables_dict[object_node_variable].__class__ == ObjectNode:
                    variables_manager.variables_dict[object_node_variable].properties[
                        PropertyNode(property_name)] = variables_manager.variables_dict[value_node_variable]
                else:
                    variables_manager.variables_dict[object_node_variable] = ObjectNode(
                        variable=object_node_variable,
                        properties={PropertyNode(property_name): variables_manager.variables_dict[value_node_variable]})
            at_t_expression_string = "{from: " + value_node_variable + ".intervalFrom, to: " + value_node_variable + ".intervalTo}"
            interval_variable = value_node_variable

        at_t_expression_type = {"from": "property", "to": "property"}
        for index, time_property in enumerate(at_t_expression.time_property_chains):
            if index == 0:
                if time_property.upper() == "FROM":
                    at_t_expression_string = interval_variable + ".intervalFrom"
                elif time_property.upper() == "TO":
                    at_t_expression_string = interval_variable + ".intervalTo"
                at_t_expression_type = "property"
            else:
                at_t_expression_string = at_t_expression_string + '.' + time_property
        return at_t_expression_string, at_t_expression_type

    @staticmethod
    def convert_atom(atom: Atom, variables_manager) -> (str,):
        atom = atom.atom
        if atom.__class__ == str:
            return ExpressionConverter.convert_literal(atom, variables_manager)
        elif atom.__class__ == ListLiteral:
            return ExpressionConverter.convert_list_literal(atom, variables_manager)
        elif atom.__class__ == MapLiteral:
            return ExpressionConverter.convert_map_literal(atom, variables_manager)
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
            parenthesized_expression_string, parenthesized_expression_type = ExpressionConverter.convert_expression(
                atom.expression, variables_manager)
            return '(' + parenthesized_expression_string + ')', parenthesized_expression_type
        elif atom.__class__ == FunctionInvocation:
            return ExpressionConverter.convert_function_invocation(atom, variables_manager)
        elif atom.__class__ == ExistentialSubquery:
            pass
        return "", None

    @staticmethod
    def convert_literal(literal: str, variables_manager) -> (str,):
        if literal.upper() == "NOW" and literal not in variables_manager.variables_dict.keys():
            return "\"" + literal + "\"", "property"
        # property属性类型，包括数值类，字符类，布尔类，空间类和时间类（时间点和时间段）
        if re.match(r"[A-Za-z]\w*", literal) and literal in variables_manager.variables_dict.keys():
            # 为变量名
            return literal, variables_manager.variables_dict[literal]
        return literal, "property"

    @staticmethod
    def convert_list_literal(list_literal: ListLiteral, variables_manager) -> (str,):
        list_literal_string, list_literal_type = "", []
        for index, expression in enumerate(list_literal.expressions):
            if index != 0:
                list_literal_string = list_literal_string + ", "
            expression_string, expression_type = ExpressionConverter.convert_expression(expression, variables_manager)
            list_literal_string = list_literal_string + expression_string
            list_literal_type.append(expression_type)
        list_literal_string = '[' + list_literal_string + ']'
        return list_literal_string, list_literal_type

    @staticmethod
    def convert_map_literal(map_literal: MapLiteral, variables_manager) -> (str,):
        map_literal_string, map_literal_type = "", {}
        for index, (key, value) in enumerate(map_literal.keys_values.items()):
            if index != 0:
                map_literal_string = map_literal_string + ", "
            value_string, value_type = ExpressionConverter.convert_expression(value, variables_manager)
            map_literal_string = map_literal_string + key + ": " + value_string
            map_literal_type[key] = value_type
        map_literal_string = '{' + map_literal_string + '}'
        return map_literal_string, map_literal_type

    @staticmethod
    def convert_function_invocation(function_invocation: FunctionInvocation, variables_manager) -> (str,):
        function_invocation_string, function_invocation_type = "", None
        if function_invocation.is_distinct:
            function_invocation_string = "DISTINCT "
        if GlobalVariables.function_info[function_invocation.function_name] == ["expression"]:
            # 返回类型由输入参数决定，例如collect
            function_invocation_type = []
        else:
            function_invocation_type = GlobalVariables.function_info[function_invocation.function_name]
        for index, expression in enumerate(function_invocation.expressions):
            if index != 0:
                function_invocation_string = function_invocation_string + ", "
            expression_string, expression_type = ExpressionConverter.convert_expression(expression, variables_manager)
            function_invocation_string = function_invocation_string + expression_string
            if GlobalVariables.function_info[function_invocation.function_name] == ["expression"]:
                function_invocation_type.append(expression_type)
        if function_invocation.function_name in GlobalVariables.scypher_function_info.keys():
            function_invocation_string = "scypher." + function_invocation.function_name + '(' + function_invocation_string + ')'
        else:
            function_invocation_string = function_invocation.function_name + '(' + function_invocation_string + ')'
        return function_invocation_string, function_invocation_type
