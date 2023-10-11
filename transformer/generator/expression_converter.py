from transformer.ir.s_expression import *


class ExpressionConverter:
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
        comparison_string = self.convert_comparison_expression(not_expression.comparison_expression)
        if not_expression.is_not:
            comparison_string = 'not ' + comparison_string
        return comparison_string

    def convert_comparison_expression(self, comparison_expression: ComparisonExpression) -> str:
        comparison_string = self.convert_subject_expression(comparison_expression.subject_expressions[0])
        for index, comparison_operation in enumerate(comparison_expression.comparison_operations):
            comparison_string = comparison_string + ' ' + comparison_operation + ' ' + self.convert_subject_expression(
                comparison_expression.subject_expressions[index + 1])
        return comparison_string

    def convert_subject_expression(self, subject_expression: SubjectExpression) -> str:
        subject_string = self.convert_add_subtract_expression(subject_expression.add_or_subtract_expression)
        predicate_expression = subject_expression.predicate_expression
        if predicate_expression:
            if predicate_expression.__class__ == TimePredicateExpression:
                predicate_string = self.convert_add_subtract_expression(predicate_expression.add_or_subtract_expression)
                return "scypher." + predicate_expression.time_operation.lower() + "(" + subject_string + ", " + predicate_string + ")"
            elif predicate_expression.__class__ == StringPredicateExpression:
                predicate_string = self.convert_add_subtract_expression(predicate_expression.add_or_subtract_expression)
                return subject_string + ' ' + predicate_expression.string_operation + ' ' + predicate_string
            elif predicate_expression.__class__ == ListPredicateExpression:
                predicate_string = self.convert_add_subtract_expression(predicate_expression.add_or_subtract_expression)
                return subject_string + ' IN ' + predicate_string
            elif predicate_expression.__class__ == NullPredicateExpression:
                if predicate_expression.is_null:
                    return subject_string + " IS NULL"
                return subject_string + " IS NOT NULL"
        return subject_string

    def convert_add_subtract_expression(self, add_or_subtract_expression: AddSubtractExpression) -> str:
        add_subtract_string = self.convert_multiply_divide_expression(
            add_or_subtract_expression.multiply_divide_expressions[0])
        for index, add_subtract_operation in enumerate(add_or_subtract_expression.add_subtract_operations):
            add_subtract_string = add_subtract_string + ' ' + add_subtract_operation + ' ' + self.convert_multiply_divide_expression(
                add_or_subtract_expression.multiply_divide_expressions[index + 1])
        return add_subtract_string

    def convert_multiply_divide_expression(self, multiply_divide_expression: MultiplyDivideExpression) -> str:
        multiply_divide_string = self.convert_power_expression(multiply_divide_expression.power_expressions[0])
        for index, multiply_divide_operation in enumerate(multiply_divide_expression.multiply_divide_operations):
            multiply_divide_string = multiply_divide_string + ' ' + multiply_divide_operation + ' ' + self.convert_power_expression(
                multiply_divide_expression.power_expressions[index + 1])
        return multiply_divide_string

    def convert_power_expression(self, power_expression: PowerExpression) -> str:
        power_string = self.convert_list_index_expression(power_expression.list_index_expressions[0])
        for index, list_index_expression in enumerate(power_expression.list_index_expressions):
            if index != 0:
                power_string = power_string + '^' + self.convert_list_index_expression(list_index_expression)
        return power_string

    def convert_list_index_expression(self, list_index_expression: ListIndexExpression) -> str:
        list_index_string = ""
        if list_index_expression.principal_expression.__class__ == PropertiesLabelsExpression:
            list_index_string = self.convert_properties_labels_expression(list_index_expression.principal_expression)
        elif list_index_expression.principal_expression.__class__ == AtTExpression:
            list_index_string = self.convert_at_t_expression(list_index_expression.principal_expression)

        for index_expression in list_index_expression.index_expressions:
            if index_expression.right_expression is None:
                list_index_string = list_index_string + '[' + index_expression.left_expression.convert() + ']'
            else:
                list_index_string = list_index_string + '[' + index_expression.left_expression.convert() + " .. " + index_expression.right_expression.convert() + ']'

        if list_index_expression.is_positive is False:
            list_index_string = '-' + list_index_string
        return list_index_string

    def convert_properties_labels_expression(self, properties_labels_expression: PropertiesLabelsExpression) -> str:
        properties_labels_expression_string = self.convert_atom(properties_labels_expression.atom)
        for proprety in properties_labels_expression.property_chains:
            properties_labels_expression_string = properties_labels_expression_string + '.' + proprety
        for label in properties_labels_expression.labels:
            properties_labels_expression_string = properties_labels_expression_string + ':' + label
        return properties_labels_expression_string

    def convert_at_t_expression(self, at_t_expression: AtTExpression) -> str:
        at_t_expression_string = self.convert_atom(at_t_expression.atom)
        for proprety in at_t_expression.property_chains:
            at_t_expression_string = at_t_expression_string + '.' + proprety
        if at_t_expression.is_value:
            at_t_expression_string = at_t_expression_string + "#Value"
        at_t_expression_string = at_t_expression_string + "@T"
        for time_proprety in at_t_expression.time_property_chains:
            at_t_expression_string = at_t_expression_string + '.' + time_proprety
        return at_t_expression_string

    def convert_atom(self, atom: Atom) -> str:
        atom = atom.atom
        atom_string = ""
        if atom.__class__ == str:
            return atom
        elif atom.__class__ == ListLiteral:
            for index, expression in enumerate(atom.expressions):
                if index != 0:
                    atom_string = atom_string + ", "
                atom_string = atom_string + self.convert_expression(expression)
            atom_string = '[' + atom_string + ']'
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
            if atom.is_distinct:
                atom_string = "DISTINCT "
            for index, expression in enumerate(atom.expressions):
                if index != 0:
                    atom_string = atom_string + ", "
                atom_string = atom_string + self.convert_expression(expression)
            atom_string = atom.function_name + '(' + atom_string + ')'
        elif atom.__class__ == ExistentialSubquery:
            pass
        return atom_string

    def convert_map_literal(self, map_literal: MapLiteral) -> str:
        map_literal_string = ""
        for index, (key, value) in enumerate(map_literal.keys_values.items()):
            if index != 0:
                map_literal_string = map_literal_string + ", "
            map_literal_string = map_literal_string + key + ": " + self.convert_expression(value)
        map_literal_string = '{' + map_literal_string + '}'
        return map_literal_string
