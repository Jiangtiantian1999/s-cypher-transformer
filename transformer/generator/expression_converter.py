from transformer.conf.config_reader import ConfigReader
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_expression import *
from transformer.ir.s_graph import *


class ExpressionConverter:

    def __init__(self, variables_manager: VariablesManager):
        self.variables_manager = variables_manager

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
        add_subtract_expression_string = self.convert_multiply_divide_modulo_expression(
            add_subtract_expression.multiply_divide_modulo_expressions[0])

        for index, add_subtract_operation in enumerate(add_subtract_expression.add_subtract_operations):
            add_subtract_expression_string = add_subtract_expression_string + ' ' + add_subtract_operation + ' ' + self.convert_multiply_divide_modulo_expression(
                add_subtract_expression.multiply_divide_modulo_expressions[index + 1])

        return add_subtract_expression_string

    def convert_multiply_divide_modulo_expression(self,
                                                  multiply_divide_modulo_expression: MultiplyDivideModuloExpression) -> str:
        multiply_divide_modulo_expression_string = self.convert_power_expression(
            multiply_divide_modulo_expression.power_expressions[0])

        for index, multiply_divide_operation in enumerate(
                multiply_divide_modulo_expression.multiply_divide_modulo_operations):
            multiply_divide_modulo_expression_string = multiply_divide_modulo_expression_string + ' ' + multiply_divide_operation + ' ' + self.convert_power_expression(
                multiply_divide_modulo_expression.power_expressions[index + 1])
        return multiply_divide_modulo_expression_string

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

    def convert_time_point_literal(self, time_point_literal: TimePointLiteral) -> str:
        if time_point_literal.time_point.__class__ == str:
            return time_point_literal.time_point
        else:
            return self.convert_map_literal(time_point_literal.time_point)

    def convert_at_t_element(self, at_t_element: AtTElement = None) -> str:
        if at_t_element is None:
            return None
        interval_from_string = self.convert_time_point_literal(at_t_element.interval_from)
        if at_t_element.interval_to:
            interval_to_string = self.convert_time_point_literal(at_t_element.interval_to)
            return "scypher.interval(" + interval_from_string + ", " + interval_to_string + ')'
        else:
            return "scypher.timePoint(" + interval_from_string + ')'

    def get_property_value(self, variable_name: str, property_name: str, time_window: AtTElement = None) -> str:
        if time_window:
            time_window_string = self.convert_at_t_element(time_window)
        else:
            time_window_string = "NULL"
        # 实际上variable_name可能为对象节点/边/Map，scypher.variable_name函数内部应该加以区分
        return "scypher.getPropertyValue(" + variable_name + ", \"" + property_name + "\", " + time_window_string + ')'

    def convert_properties_labels_expression(self, properties_labels_expression: PropertiesLabelsExpression) -> str:
        properties_labels_expression_string = self.convert_atom(properties_labels_expression.atom)
        for property_lookup in properties_labels_expression.property_chains:
            properties_labels_expression_string = self.get_property_value(properties_labels_expression_string,
                                                                          property_lookup.property_name,
                                                                          property_lookup.time_window)

        for label in properties_labels_expression.labels:
            # 判断某节点/边是否有某（些）标签
            properties_labels_expression_string = properties_labels_expression_string + ':' + label
        return properties_labels_expression_string

    def convert_at_t_expression(self, at_t_expression: AtTExpression) -> str:
        at_t_expression_string = self.convert_atom(at_t_expression.atom)
        for index, property_lookup in enumerate(at_t_expression.property_chains):
            at_t_expression_string = self.get_property_value(at_t_expression_string, property_lookup.property_name,
                                                             property_lookup.time_window)
        # 所查询的对象节点
        element_variable = at_t_expression_string
        if at_t_expression.property_name is None:
            # 返回对象节点或边的有效时间，直接访问即可
            interval = {"from": element_variable + ".intervalFrom", "to": element_variable + ".intervalTo"}
        elif at_t_expression.time_window is None:
            # 返回属性节点的有效时间
            # 实际上object_variable.property_name也可能为对象节点，scypher.getPropertyEffectiveTime函数内部应该加以区分
            interval = "scypher.getPropertyEffectiveTime(" + element_variable + ", \"" + at_t_expression.property_name + "\")"
        else:
            # 返回值节点的有效时间
            if at_t_expression.time_window.__class__ == AtTExpression:
                interval_string = self.convert_at_t_element(at_t_expression.time_window)
            else:
                interval_string = "NULL"
            # 一定是返回值节点的有效时间，否则报错
            interval = "scypher.getValueEffectiveTime(" + element_variable + ", \"" + at_t_expression.property_name + "\", " + interval_string + ')'

        for index, time_property in enumerate(at_t_expression.time_property_chains):
            if index == 0:
                if interval.__class__ == dict:
                    if time_property in ["from", "to"]:
                        interval = interval[time_property]
                    else:
                        interval = "NULL"
                else:
                    interval = interval + '.' + time_property
        if interval.__class__ == dict:
            return "{\"from\":" + interval["from"] + ", \"to\":" + interval["to"] + '}'
        return interval

    def convert_atom(self, atom: Atom) -> str:
        particle = atom.particle
        if particle.__class__ == str:
            if particle.upper() == "NOW" and particle not in self.variables_manager.user_variables:
                particle = "\"NOW\""
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
