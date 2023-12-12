from transformer.grammar_parser.s_cypherListener import s_cypherListener
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *
from transformer.ir.s_expression import *
from transformer.exceptions.s_exception import *
from queue import Queue


# This class records important information about the query
class SCypherWalker(s_cypherListener):
    def __init__(self, parser: s_cypherParser):
        self.parser = parser

        # node
        self.properties = None
        self.properties_pattern = dict()  # 对象节点的属性 dict[PropertyNode, ValueNode]
        self.properties_parameter = None
        self.property_node_list = []  # 属性节点列表
        self.value_node_list = []  # 值节点列表
        self.node_labels = []
        self.object_node_time_window = None
        self.property_node_time_window = None
        self.value_node_time_window = None

        # time
        self.at_time_clause = None
        self.at_t_element = None
        self.time_point_literals = []

        # pattern
        self.patterns = []
        self.object_node_list = []
        self.edge_list = []  # 存放所有边
        self.relationship_pattern = None  # 边模式SEdge
        self.pattern_element = None  # SPath
        self.path_function_pattern = None  # TemporalPathCall
        self.rel_type_names = []  # 边标签
        self.rel_length_range = None  # 边长度区间
        self.pattern_part_list = []
        self.single_path_pattern = None

        # clauses
        self.query_clause = None
        self.single_query_clauses = []
        self.multi_part_query_clauses = []
        self.single_part_query_clause = None
        self.union_query_clause = None
        self.with_clause = None
        self.with_query_clauses = []
        self.time_window_limit_clause = None  # 时间窗口限定
        self.snapshot_clause = None
        self.scope_clause = None

        self.reading_clauses = []
        self.match_clause = None
        self.unwind_clause = None
        self.in_query_call_clause = None
        self.stand_alone_call_clause = None
        self.return_clause = None
        self.between_clause = None
        self.order_by_clause = None
        self.yield_clause = None

        # UpdatingClause
        self.updating_clauses = []
        self.create_clause = None
        self.merge_clause = None
        self.delete_clause = None
        self.set_clause = None
        self.remove_clause = None
        self.stale_clause = None

        # expression
        self.skip_expression = Stack()
        self.limit_expression = Stack()
        self.expression = Stack()
        self.or_expression = Stack()
        self.xor_expressions = Stack()
        self.and_expressions = Stack()
        self.not_expressions = Stack()
        self.comparison_expression = Stack()
        self.subject_expressions = Stack()
        self.string_list_null_predicate_expression = Stack()
        self.null_predicate_expression = Stack()
        self.list_predicate_expression = Stack()
        self.string_predicate_expression = Stack()
        self.time_predicate_expression = Stack()
        self.add_subtract_expression = Stack()  # 第一个是oC_StringListNullPredicateExpression里的，第二个是PredicateExpression里的
        self.multiply_divide_modulo_expressions = Stack()
        self.power_expressions = Stack()
        self.list_index_expressions = Stack()
        self.index_expressions = Stack()
        self.AtT_expression = Stack()
        self.properties_labels_expression = Stack()
        self.remove_property_expression = Stack()
        self.set_property_expression = Stack()
        self.principal_expression = Stack()
        self.list_expression = Stack()
        self.back_expression = Stack()
        self.filter_where_expression = Stack()
        self.left_expression = Stack()
        self.right_expression = Stack()
        self.where_expression = Stack()
        self.case_expression = Stack()
        self.parenthesized_expression = Stack()
        self.function_invocation = Stack()
        self.function_invocation_expressions = Stack()
        self.list_literal_expressions = Stack()

        # Atom
        self.atom = None
        self.list_literal = None
        self.map_literal = None
        # self.case_expression = None
        self.list_comprehension = None
        self.pattern_comprehension = None
        self.quantifier = None
        self.pattern_predicate = None
        # self.parenthesized_expression = None
        # self.function_invocation = None
        self.existential_subquery = None
        # self.function_invocation_expressions = []

        # 中间变量
        self.projection_items = []
        self.sort_items = dict()
        self.yield_items = []
        self.explicit_input_items = Stack()  # 带参程序调用
        self.delete_items = []
        self.set_items = []
        self.remove_items = []
        self.stale_items = []
        self.merge_actions = dict()
        self.property_look_up_list = []
        self.property_look_up_time_list = []
        self.property_look_up_name = None
        self.procedure_name = None
        self.add_subtract_operations = Stack()
        self.multiply_divide_module_operations = Stack()
        self.power_operations = Stack()
        self.comparison_operations = Stack()
        self.map_key_values = dict()
        self.integer_literals = []
        self.rel_properties = None

        # bool
        self.union_is_all_list = []
        self.is_explicit = False
        self.projection_item_is_all = False
        self.is_property_look_up_time = False
        self.is_set = False
        self.is_remove = False

    def exitOC_Query(self, ctx: s_cypherParser.OC_QueryContext):
        if ctx.oC_RegularQuery():
            self.query_clause = self.union_query_clause
        elif ctx.oC_StandaloneCall() is not None:
            self.query_clause = self.stand_alone_call_clause
        elif ctx.s_TimeWindowLimit() is not None:
            self.query_clause = self.time_window_limit_clause

    # 多个SingleQuery，用UNION/UNION ALL连接，其中SingleQuery有可能是单个SinglePartQuery，也有可能是MultiPartQuery_clauses
    def exitOC_RegularQuery(self, ctx: s_cypherParser.OC_RegularQueryContext):
        # multi_query_clauses: List[MultiQueryClause],
        # is_all: List[bool]
        self.union_query_clause = UnionQueryClause(self.single_query_clauses, self.union_is_all_list)
        self.single_query_clauses = []  # 退出清空
        self.union_is_all_list = []

    # 获取UNION/UNION ALL
    def enterOC_Union(self, ctx: s_cypherParser.OC_UnionContext):
        if ctx.UNION() is not None:
            if ctx.UNION() is not None and ctx.ALL() is not None:
                self.union_is_all_list.append(True)
            else:
                self.union_is_all_list.append(False)

    # 处理WithQueryClause
    def exitS_WithPartQuery(self, ctx: s_cypherParser.S_WithPartQueryContext):
        # with_clause: WithClause,
        # reading_clauses: List[ReadingClause] = None,
        # updating_clauses: List[UpdatingClause] = None
        with_clause = self.with_clause
        reading_clauses = self.reading_clauses
        updating_clauses = self.updating_clauses
        # 退出清空
        self.with_clause = None
        self.reading_clauses = []
        self.updating_clauses = []
        self.with_query_clauses.append(WithQueryClause(with_clause, reading_clauses, updating_clauses))

    def exitOC_UpdatingClause(self, ctx: s_cypherParser.OC_UpdatingClauseContext):
        # update_clause: CreateClause | DeleteClause | StaleClause | SetClause | MergeClause | RemoveClause,
        update_clause = None
        if ctx.s_Create() is not None:
            update_clause = self.create_clause
            self.create_clause = None
        elif ctx.s_Merge() is not None:
            update_clause = self.merge_clause
            self.merge_clause = None
        elif ctx.s_Delete() is not None:
            update_clause = self.delete_clause
            self.delete_clause = None
        elif ctx.s_Set() is not None:
            update_clause = self.set_clause
            self.set_clause = None
        elif ctx.oC_Remove() is not None:
            update_clause = self.remove_clause
            self.remove_clause = None
        elif ctx.s_Stale() is not None:
            update_clause = self.stale_clause
            self.stale_clause = None
        self.updating_clauses.append(UpdatingClause(update_clause))

    def exitOC_MultiPartQuery(self, ctx: s_cypherParser.OC_MultiPartQueryContext):
        # single_query_clause: SingleQueryClause = None,
        # with_query_clauses: List[WithQueryClause] = None
        self.multi_part_query_clauses.append(MultiQueryClause(self.single_part_query_clause, self.with_query_clauses))
        self.single_part_query_clause = None
        self.with_query_clauses = []  # 退出清空

    # SinglePartQuery或者MultiPartQuery
    def exitOC_SingleQuery(self, ctx: s_cypherParser.OC_SingleQueryContext):
        if len(self.multi_part_query_clauses) > 0:
            # self.single_query_clauses.append(self.multi_part_query_clauses)
            self.single_query_clauses = self.multi_part_query_clauses
            self.multi_part_query_clauses = []  # 退出清空
        else:
            self.single_query_clauses.append(MultiQueryClause(self.single_part_query_clause, None))
            self.single_part_query_clause = None

    def exitOC_SinglePartQuery(self, ctx: s_cypherParser.OC_SinglePartQueryContext):
        # reading_clauses: List[ReadingClause] = None,
        # updating_clauses: List[UpdatingClause] = None,
        # return_clause: ReadingClause
        self.single_part_query_clause = SingleQueryClause(self.reading_clauses, self.updating_clauses,
                                                          self.return_clause)
        self.reading_clauses = []  # 退出清空
        self.updating_clauses = []
        self.return_clause = None

    def exitS_With(self, ctx: s_cypherParser.S_WithContext):
        # projection_items: List[ProjectionItem] = None,
        # is_all: bool = False,
        # is_distinct: bool = False,
        # where_expression: Expression = None,
        # order_by_clause: OrderByClause = None,
        # skip_expression: Expression = None,
        # limit_expression: Expression = None
        projection_items = self.projection_items
        self.projection_items = []  # 退出清空
        is_all = self.projection_item_is_all
        self.projection_item_is_all = False
        is_distinct = False
        if ctx.oC_ProjectionBody().DISTINCT() is not None:
            is_distinct = True
        if ctx.oC_Where() is not None:
            where_expression = self.where_expression.pop()
        else:
            where_expression = None
        if ctx.oC_ProjectionBody().oC_Order() is not None:
            order_by_clause = self.order_by_clause
            self.order_by_clause = None  # 退出清空
        else:
            order_by_clause = None
        if ctx.oC_ProjectionBody().oC_Skip() is not None:
            skip_expression = self.skip_expression.pop()
        else:
            skip_expression = None
        if ctx.oC_ProjectionBody().oC_Limit() is not None:
            limit_expression = self.limit_expression.pop()
        else:
            limit_expression = None

        self.with_clause = WithClause(projection_items, is_all, is_distinct, where_expression, order_by_clause,
                                      skip_expression, limit_expression)

    def exitOC_ReadingClause(self, ctx: s_cypherParser.OC_ReadingClauseContext):
        # reading_clause: MatchClause | UnwindClause | CallClause
        if self.match_clause is not None:
            reading_clause = ReadingClause(self.match_clause)
            self.match_clause = None  # 退出清空
        elif self.unwind_clause is not None:
            reading_clause = ReadingClause(self.unwind_clause)
            self.unwind_clause = None  # 退出清空
        elif self.in_query_call_clause is not None:
            reading_clause = ReadingClause(self.in_query_call_clause)
            self.in_query_call_clause = None  # 退出清空
        else:
            raise ValueError("The reading clause must have a clause which is not None among MatchClause, UnwindClause "
                             "and CallClause.")
        self.reading_clauses.append(reading_clause)

    def exitOC_Match(self, ctx: s_cypherParser.OC_MatchContext):
        # patterns: List[Pattern],
        # is_optional: bool = False,
        # where_expression: Expression = None,
        # time_window: AtTimeClause | BetweenClause = None
        is_optional = False
        patterns = []
        time_window = None
        where_expression = None
        if ctx.OPTIONAL() is not None:
            is_optional = True
        if ctx.oC_Pattern() is not None:
            patterns = self.patterns
            self.patterns = []  # 退出清空
        if ctx.s_AtTime() is not None:
            time_window = self.at_time_clause
            self.at_time_clause = None  # 退出清空
        elif ctx.s_Between() is not None:
            time_window = self.between_clause
            self.between_clause = None  # 退出清空
        if ctx.oC_Where() is not None:
            where_expression = self.where_expression.pop()
        self.match_clause = MatchClause(patterns, is_optional, where_expression, time_window)

    def exitS_Between(self, ctx: s_cypherParser.S_BetweenContext):
        # interval: Expression
        if self.expression.is_empty() is False:
            interval = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        self.between_clause = BetweenClause(interval)

    def exitS_AtTime(self, ctx: s_cypherParser.S_AtTimeContext):
        if self.expression.is_empty() is False:
            expression = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        self.at_time_clause = AtTimeClause(expression)

    def exitOC_Unwind(self, ctx: s_cypherParser.OC_UnwindContext):
        # expression: Expression,
        # variable: str
        if self.expression.is_empty() is False:
            expression = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        variable = ctx.oC_Variable().getText()
        self.unwind_clause = UnwindClause(expression, variable)

    def exitOC_InQueryCall(self, ctx: s_cypherParser.OC_InQueryCallContext):
        # procedure_name: str,
        # input_items: List[Expression] = None,
        # yield_clause: YieldClause = None
        if ctx.oC_ExplicitProcedureInvocation() is not None:
            input_items = self.explicit_input_items.pop()
        else:
            tmp = self.explicit_input_items.pop()
            input_items = None
        self.in_query_call_clause = CallClause(self.procedure_name, input_items, self.yield_clause)
        self.yield_clause = None
        self.procedure_name = None

    def enterOC_ProcedureName(self, ctx: s_cypherParser.OC_ProcedureNameContext):
        self.procedure_name = ctx.getText()

    def exitS_YieldItems(self, ctx: s_cypherParser.S_YieldItemsContext):
        # yield_items: List[YieldItem] = None,
        # is_all=False,
        # where_expression: Expression = None
        if self.where_expression.is_empty() is False:
            where_expression = self.where_expression.pop()
        else:
            where_expression = None
        self.yield_clause = YieldClause(self.yield_items, False, where_expression)
        self.yield_items = []  # 退出清空

    def exitS_YieldItem(self, ctx: s_cypherParser.S_YieldItemContext):
        # procedure_result: str,
        # variable: str = None
        if ctx.oC_ProcedureResultField() is not None:
            procedure_result = ctx.oC_ProcedureResultField().getText()
        else:
            procedure_result = None
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        else:
            variable = None
        self.yield_items.append(YieldItem(procedure_result, variable))

    # CALL查询
    def exitOC_StandaloneCall(self, ctx: s_cypherParser.OC_StandaloneCallContext):
        # procedure_name: str,
        # input_items: List[Expression] = None,
        # yield_clause: YieldClause = None
        if ctx.oC_ExplicitProcedureInvocation() is not None:
            input_items = self.explicit_input_items.pop()
        else:
            tmp = self.explicit_input_items.pop()
            input_items = None
        # 检查*
        if '*' in ctx.getText():
            yield_clause = YieldClause(None, True, None)
        else:
            yield_clause = self.yield_clause
        self.stand_alone_call_clause = CallClause(self.procedure_name, input_items, yield_clause)
        self.yield_clause = None
        self.procedure_name = None

    def enterOC_ExplicitProcedureInvocation(self, ctx: s_cypherParser.OC_ExplicitProcedureInvocationContext):
        self.is_explicit = True
        self.explicit_input_items.push([])

    def exitOC_ExplicitProcedureInvocation(self, ctx: s_cypherParser.OC_ExplicitProcedureInvocationContext):
        self.is_explicit = False

    # def enterS_ExplicitExpression(self, ctx: s_cypherParser.S_ExplicitExpressionContext):
    #     self.explicit_input_items.push([])

    def exitS_ExplicitExpression(self, ctx: s_cypherParser.S_ExplicitExpressionContext):
        self.explicit_input_items.peek().append(self.expression.pop())

    @staticmethod
    def getAtTElement(interval_str) -> AtTElement:
        index = 0
        interval_from = interval_to = None
        find_from = find_to = False
        while index < len(interval_str):
            if interval_str[index] == " ":
                index = index + 1
                continue
            elif interval_str[index] == '(':
                find_from = True
                interval_from = ""
            elif interval_str[index] == ',':
                find_to = True
                find_from = False
                interval_to = ""
            elif interval_str[index] == ')':
                break
            elif find_from:
                interval_from += interval_str[index]
            elif find_to:
                interval_to += interval_str[index]
            index = index + 1
        if interval_to == "NOW":
            at_t_element = AtTElement(TimePointLiteral(interval_from), TimePointLiteral('"NOW"'))
        else:
            at_t_element = AtTElement(TimePointLiteral(interval_from),
                                      TimePointLiteral(interval_to))
        return at_t_element

    # 获取对象节点
    def exitOC_NodePattern(self, ctx: s_cypherParser.OC_NodePatternContext):
        # node_content = ""  # 对象节点内容
        if ctx.oC_NodeLabels() is not None:
            node_label_list = self.node_labels  # 对象节点标签
            self.node_labels = []  # 退出清空
        else:
            node_label_list = None
        variable = None
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        # 对象节点时间
        time_window = None
        if ctx.s_AtTElement() is not None:
            time_window = self.at_t_element
            self.at_t_element = None
        if ctx.s_Properties() is not None:
            properties = self.properties
            self.properties = None  # 退出清空
        else:
            properties = None  # 对象节点属性
        self.object_node_list.append(ObjectNode(node_label_list, variable, time_window, properties))

    def exitOC_NodeLabel(self, ctx: s_cypherParser.OC_NodeLabelContext):
        self.node_labels.append(ctx.getText().strip(':'))

    def exitS_Properties(self, ctx: s_cypherParser.S_PropertiesContext):
        if ctx.s_PropertiesPattern() is not None:
            self.properties = self.properties_pattern
            self.properties_pattern = dict()  # 退出清空
        elif ctx.oC_Parameter() is not None:
            # TODO: 无法组成dict类型，暂以字符串处理
            self.properties = self.properties_parameter
            self.properties_parameter = None  # 退出清空
        else:
            self.properties = None

    def enterOC_Parameter(self, ctx: s_cypherParser.OC_ParameterContext):
        self.properties_parameter = ctx.getText()

    def exitS_PropertiesPattern(self, ctx: s_cypherParser.S_PropertiesPatternContext):
        # 将属性节点和值节点组合成对象节点的属性
        for prop_node, val_node in zip(self.property_node_list, self.value_node_list):
            self.properties_pattern[prop_node] = val_node
        # 退出清空
        self.property_node_list = []
        self.value_node_list = []

    def exitOC_Parameter(self, ctx: s_cypherParser.OC_ParameterContext):
        pass

    # 获取属性节点
    def exitS_PropertyNode(self, ctx: s_cypherParser.S_PropertyNodeContext):
        # 获取属性节点内容
        property_content = ctx.oC_PropertyKeyName().getText()  # 属性节点内容
        time_window = None
        # 获取属性节点的时间
        if ctx.s_AtTElement() is not None:
            time_window = self.at_t_element  # 属性节点时间
            self.at_t_element = None
        self.property_node_list.append(PropertyNode(property_content, None, time_window))

    def exitS_ValueNode(self, ctx: s_cypherParser.S_ValueNodeContext):
        value_content = None  # 值节点内容
        # 获取值节点内容
        if ctx.oC_Expression() is not None:
            if self.expression.is_empty() is False:
                value_content = self.expression.pop()
            else:
                raise ParseError("Expect expression but there is none in expression stack.")
        # 获取值节点的时间
        time_window = None  # 值节点时间
        if ctx.s_AtTElement() is not None:
            time_window = self.at_t_element
            self.at_t_element = None
        # 构造值节点
        self.value_node_list.append(ValueNode(value_content, None, time_window))

    # 获取时间
    def exitS_AtTElement(self, ctx: s_cypherParser.S_AtTElementContext):
        # interval_from: TimePointLiteral,
        # interval_to: TimePointLiteral = None
        if len(self.time_point_literals) == 2:
            self.at_t_element = AtTElement(self.time_point_literals[0], self.time_point_literals[1])
            self.time_point_literals = []  # 退出清空
        elif len(self.time_point_literals) == 1 and ctx.NOW() is not None:
            self.at_t_element = AtTElement(self.time_point_literals[0],
                                           TimePointLiteral('"NOW"'))
            self.time_point_literals = []  # 退出清空
        elif len(self.time_point_literals) == 1 and ctx.NOW() is None:
            self.at_t_element = AtTElement(self.time_point_literals[0], None)
            self.time_point_literals = []  # 退出清空
        elif len(self.time_point_literals) == 0 and ctx.NOW() is not None:
            self.at_t_element = AtTElement(TimePointLiteral('"NOW"'), None)
            self.time_point_literals = []  # 退出清空
        else:
            raise ParseError("Invalid time format!")

    def exitS_TimePointLiteral(self, ctx: s_cypherParser.S_TimePointLiteralContext):
        if ctx.oC_MapLiteral() is not None:
            self.time_point_literals.append(TimePointLiteral(self.map_literal))
            self.map_literal = None
        else:
            self.time_point_literals.append(TimePointLiteral(ctx.StringLiteral().getText()))

    def exitOC_Properties(self, ctx: s_cypherParser.OC_PropertiesContext):
        # oC_MapLiteral | oC_Parameter
        if ctx.oC_MapLiteral() is not None:
            self.rel_properties = self.map_literal
            self.map_literal = None  # 退出清空
        elif ctx.oC_Parameter() is not None:
            # TODO:oC_Parameter未处理
            pass

    def exitOC_RelationshipDetail(self, ctx: s_cypherParser.OC_RelationshipDetailContext):
        # direction: str,
        # variable: str = None,
        # labels: List[str] = None,
        # length: Tuple[int, int] = (1, 1),
        # time_window: AtTElement = None,
        # properties: dict[str, Expression] = None
        variable = None
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        interval = self.at_t_element
        self.at_t_element = None
        if ctx.oC_RangeLiteral() is not None:
            length_tuple = self.rel_length_range
        else:
            length_tuple = (1, 1)
        labels = self.rel_type_names
        self.rel_type_names = []  # 退出清空
        properties = self.rel_properties
        self.rel_properties = None  # 退出清空
        self.relationship_pattern = SRelationship('UNDIRECTED', variable, labels, length_tuple, interval, properties)

    def exitOC_RangeLiteral(self, ctx: s_cypherParser.OC_RangeLiteralContext):
        lengths = self.integer_literals
        self.integer_literals = []  # 退出清空
        # 没有指名长度时设为None，例如，
        if len(lengths) == 2:
            # 左右区间都有
            length_tuple = (int(lengths[0]), int(lengths[1]))
        elif len(lengths) == 1:
            if '*..' in ctx.getText() or '* ..' in ctx.getText():
                # 只有右区间*..2 -> (None, 2)
                length_tuple = (None, int(lengths[0]))
            # 只有左区间
            elif '*' in ctx.getText() and '..' in ctx.getText():
                # *2.. -> (2, None)
                length_tuple = (int(lengths[0]), None)
            else:
                length_tuple = (int(lengths[0]), int(lengths[0]))
        else:
            # * -> (None, None)
            length_tuple = (None, None)
        self.rel_length_range = length_tuple

    def exitOC_IntegerLiteral(self, ctx: s_cypherParser.OC_IntegerLiteralContext):
        self.integer_literals.append(ctx.getText())

    def exitOC_RelTypeName(self, ctx: s_cypherParser.OC_RelTypeNameContext):
        self.rel_type_names.append(ctx.getText())

    def exitOC_RelationshipPattern(self, ctx: s_cypherParser.OC_RelationshipPatternContext):
        direction = 'UNDIRECTED'
        if ctx.oC_LeftArrowHead() is not None and ctx.oC_RightArrowHead() is None:
            direction = 'LEFT'
        elif ctx.oC_LeftArrowHead() is None and ctx.oC_RightArrowHead() is not None:
            direction = 'RIGHT'
        if self.relationship_pattern is not None:
            self.relationship_pattern.direction = direction
            self.edge_list.append(self.relationship_pattern)
        else:
            self.edge_list.append(SRelationship(direction))

    def exitS_PathFunctionPattern(self, ctx: s_cypherParser.S_PathFunctionPatternContext):
        # variable: str,
        # function_name: str,
        # path: SPath
        function_name = ctx.oC_FunctionName().getText()
        path = self.single_path_pattern
        self.single_path_pattern = None  # 退出清空
        self.path_function_pattern = TemporalPathCall("", function_name, path)

    def exitS_SinglePathPattern(self, ctx: s_cypherParser.S_SinglePathPatternContext):
        self.single_path_pattern = SPath(self.object_node_list, self.edge_list, None)
        self.object_node_list = []  # 退出清空
        self.edge_list = []  # 退出清空

    def exitOC_PatternElement(self, ctx: s_cypherParser.OC_PatternElementContext):
        # nodes: List[ObjectNode],
        # edges: List[SEdge] = None,
        # variable: str = None
        nodes = self.object_node_list
        edges = self.edge_list
        self.object_node_list = []  # 退出清空
        self.edge_list = []  # 退出清空
        self.pattern_element = SPath(nodes, edges)

    def exitOC_PatternPart(self, ctx: s_cypherParser.OC_PatternPartContext):
        # pattern: SPath | TemporalPathCall
        if ctx.s_PathFunctionPattern() is not None:
            if ctx.oC_Variable() is not None:
                variable = ctx.oC_Variable().getText()
                self.path_function_pattern.variable = variable
            else:
                raise ParseError("The path has no variable!")
            pattern = Pattern(self.path_function_pattern)
        elif ctx.oC_AnonymousPatternPart() is not None:
            if ctx.oC_Variable() is not None:
                variable = ctx.oC_Variable().getText()
                self.pattern_element.variable = variable
            pattern = Pattern(self.pattern_element)
        else:
            raise ParseError("The path pattern format is wrong!")
        self.patterns.append(pattern)

    def exitOC_Return(self, ctx: s_cypherParser.OC_ReturnContext):
        # projection_items: List[ProjectionItem] = None,
        # is_all: bool = False,
        # is_distinct: bool = False,
        # order_by_clause: OrderByClause = None,
        # skip_expression: Expression = None,
        # limit_expression: Expression = None
        projection_items = self.projection_items
        self.projection_items = []  # 退出清空
        is_distinct = False
        if ctx.oC_ProjectionBody() and ctx.oC_ProjectionBody().DISTINCT() is not None:
            is_distinct = True
        if ctx.oC_ProjectionBody().oC_Order() is not None:
            order_by_clause = self.order_by_clause
            self.order_by_clause = None  # 退出清空
        else:
            order_by_clause = None
        if ctx.oC_ProjectionBody().oC_Skip() is not None:
            skip_expression = self.skip_expression.pop()
        else:
            skip_expression = None
        if ctx.oC_ProjectionBody().oC_Limit() is not None:
            limit_expression = self.limit_expression.pop()
        else:
            limit_expression = None
        is_all = self.projection_item_is_all
        self.projection_item_is_all = False
        self.return_clause = ReturnClause(projection_items, is_all, is_distinct, order_by_clause, skip_expression,
                                          limit_expression)

    def exitOC_ProjectionItems(self, ctx: s_cypherParser.OC_ProjectionItemsContext):
        if ctx.getText()[0] == '*':
            self.projection_item_is_all = True

    def exitOC_ProjectionItem(self, ctx: s_cypherParser.OC_ProjectionItemContext):
        # expression: Expression,
        # variable: str = None
        variable = None
        if self.expression.is_empty() is False:
            expression = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        self.projection_items.append(ProjectionItem(expression, variable))

    def exitOC_Order(self, ctx: s_cypherParser.OC_OrderContext):
        # sort_items: dict[Expression, str]
        self.order_by_clause = OrderByClause(self.sort_items)
        self.sort_items = dict()  # 退出清空

    def exitOC_SortItem(self, ctx: s_cypherParser.OC_SortItemContext):
        if self.expression.is_empty() is False:
            expression = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        string = None
        if ctx.ASCENDING() is not None:
            string = 'ASCENDING'
        elif ctx.ASC() is not None:
            string = 'ASC'
        elif ctx.DESCENDING() is not None:
            string = 'DESCENDING'
        elif ctx.DESC() is not None:
            string = 'DESC'
        self.sort_items[expression] = string

    def exitOC_Skip(self, ctx: s_cypherParser.OC_SkipContext):
        if self.expression.is_empty() is False:
            self.skip_expression.push(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def exitOC_Limit(self, ctx: s_cypherParser.OC_LimitContext):
        if self.expression.is_empty() is False:
            self.limit_expression.push(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def exitOC_PropertyLookup(self, ctx: s_cypherParser.OC_PropertyLookupContext):
        # property_name: str
        property_name = ctx.oC_PropertyKeyName().getText()
        self.property_look_up_list.append(property_name)

    def exitS_TimePropertyItem(self, ctx: s_cypherParser.S_TimePropertyItemContext):
        self.property_look_up_time_list.append(ctx.oC_PropertyKeyName().getText())

    # 更新语句
    def exitS_Create(self, ctx: s_cypherParser.S_CreateContext):
        # patterns: List[Pattern],
        # at_time_clause: AtTimeClause = None
        patterns = self.patterns
        at_time_clause = self.at_time_clause
        self.at_time_clause = None  # 退出清空
        self.patterns = []  # 退出时清空，避免重复记录
        self.create_clause = CreateClause(patterns, at_time_clause)

    def exitS_Merge(self, ctx: s_cypherParser.S_MergeContext):
        # pattern: Pattern,
        # actions: dict[str, SetClause] = None,
        # at_time_clause: AtTimeClause = None
        if len(self.patterns) == 1:
            pattern = self.patterns[0]
            self.patterns = []  # 退出清空
        else:
            raise ValueError("The number of pattern in Merge Tree should be 1.")
        if len(self.merge_actions) > 0:
            actions = self.merge_actions
            self.merge_actions = dict()  # 退出清空
        else:
            actions = None
        at_time_clause = self.at_time_clause
        self.at_time_clause = None  # 退出清空
        self.merge_clause = MergeClause(pattern, actions, at_time_clause)

    def exitOC_MergeAction(self, ctx: s_cypherParser.OC_MergeActionContext):
        merge_flag = 'CREATE'
        if ctx.MATCH() is not None:
            merge_flag = 'MATCH'
        self.merge_actions[merge_flag] = self.set_clause

    def exitS_Delete(self, ctx: s_cypherParser.S_DeleteContext):
        # delete_items: List[DeleteItem],
        # is_detach=False,
        # time_window: AtTimeClause | BetweenClause = None
        is_detach = False
        if ctx.DETACH() is not None:
            is_detach = True
        time_window = None
        if ctx.s_AtTime() is not None:
            time_window = self.at_time_clause
            self.at_time_clause = None  # 退出时清空
        elif ctx.s_Between() is not None:
            time_window = self.between_clause
            self.between_clause = None  # 退出时清空
        self.delete_clause = DeleteClause(self.delete_items, is_detach, time_window)
        self.delete_items = []  # 退出时清空，避免重复记录

    def exitS_DeleteItem(self, ctx: s_cypherParser.S_DeleteItemContext):
        # expression: Expression,
        # property_name: str = None,
        # time_window: bool | AtTElement = None
        if self.expression.is_empty() is False:
            expression = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        property_name = None
        if ctx.s_PropertyLookupName() is not None:
            property_name = self.property_look_up_name
            self.property_look_up_name = None
        time_window = None
        if ctx.s_AtTElement() is not None:
            time_window = self.at_t_element
            self.at_t_element = None  # 退出时清空
        elif ctx.PoundValue() is not None:
            time_window = True
        self.delete_items.append(DeleteItem(expression, property_name, time_window))

    def enterS_Set(self, ctx: s_cypherParser.S_SetContext):
        self.is_set = True

    def exitS_Set(self, ctx: s_cypherParser.S_SetContext):
        # set_items: List[EffectiveTimeSetting | ExpressionSetting | LabelSetting],
        # at_time_clause: AtTimeClause = None
        at_time_clause = self.at_time_clause
        self.at_time_clause = None  # 退出清空
        self.set_clause = SetClause(self.set_items, at_time_clause)
        self.set_items = []  # 退出清空
        self.is_set = False

    def exitOC_SetItem(self, ctx: s_cypherParser.OC_SetItemContext):
        # item: EffectiveTimeSetting | ExpressionSetting | LabelSetting
        # ===NodeIntervalSetting
        # variable: str,
        # effective_time: AtTElement = None

        # ===item: EffectiveTimeSetting
        # 只有对象节点
        if (ctx.s_AtTElement() is not None and ctx.oC_Variable() is not None
                and (item is None for item in [ctx.s_SetPropertyItemOne(), ctx.s_SetPropertyItemTwo()])):
            variable = ctx.oC_Variable().getText()
            effective_time = self.at_t_element
            self.at_t_element = None
            object_setting = NodeEffectiveTimeSetting(variable, effective_time)
            # 整合SetItem
            self.set_items.append(EffectiveTimeSetting(object_setting, None, None))
        # 对象节点+属性节点
        elif all(item is not None for item in [ctx.oC_Variable(), ctx.s_SetPropertyItemOne()]):
            # 对象节点
            object_variable = ctx.oC_Variable().getText()
            object_effective_time = None
            if ctx.s_AtTElement() is not None:
                object_effective_time = self.at_t_element
                self.at_t_element = None
            object_setting = NodeEffectiveTimeSetting(object_variable, object_effective_time)
            # 属性节点
            property_variable = ctx.s_SetPropertyItemOne().oC_PropertyKeyName().getText()
            property_effective_time = self.getAtTElement(ctx.s_SetPropertyItemOne().s_AtTElement().getText())
            property_setting = NodeEffectiveTimeSetting(property_variable, property_effective_time)
            # 整合SetItem
            self.set_items.append(EffectiveTimeSetting(object_setting, property_setting, None))
        # 对象节点+属性节点+值节点
        elif all(item is not None for item in [ctx.oC_Variable(), ctx.s_SetPropertyItemTwo()]):
            # 对象节点
            object_variable = ctx.oC_Variable().getText()
            object_effective_time = None
            if ctx.s_AtTElement() is not None:
                object_effective_time = self.at_t_element
                self.at_t_element = None
            object_setting = NodeEffectiveTimeSetting(object_variable, object_effective_time)
            # 属性节点
            property_variable = ctx.s_SetPropertyItemTwo().oC_PropertyKeyName().getText()
            property_effective_time = None
            if ctx.s_SetPropertyItemTwo().s_AtTElement() is not None:
                property_effective_time = self.getAtTElement(ctx.s_SetPropertyItemTwo().s_AtTElement().getText())
            property_setting = NodeEffectiveTimeSetting(property_variable, property_effective_time)
            # 值节点
            value_effective_time = None
            if ctx.s_SetPropertyItemTwo().s_AtTElement() is not None:
                value_effective_time = self.getAtTElement(ctx.s_SetValueItem().s_AtTElement().getText())
            value_setting = value_effective_time
            # 整合SetItem
            self.set_items.append(EffectiveTimeSetting(object_setting, property_setting, value_setting))
        # ===item: LabelSetting
        elif all(item is not None for item in [ctx.oC_Variable(), ctx.oC_NodeLabels()]):
            # variable: str,
            # labels: List[str]
            variable = ctx.oC_Variable().getText()
            labels = self.node_labels
            self.node_labels = []  # 退出清空
            self.set_items.append(LabelSetting(variable, labels))
        # ===item: ExpressionSetting
        elif ctx.oC_Expression() is not None:
            # expression_left: SetPropertyExpression | str,
            # expression_right: Expression,
            # is_added: False
            if ctx.oC_PropertyExpression() is not None:
                expression_left = self.set_property_expression.pop()
            else:
                expression_left = ctx.oC_Variable().getText()
            if self.expression.is_empty() is False:
                expression_right = self.expression.pop()
            else:
                raise ParseError("Expect expression but there is none in expression stack.")
            is_added = False
            if '+=' in ctx.getText():
                is_added = True
            self.set_items.append(ExpressionSetting(expression_left, expression_right, is_added))
        else:
            raise ParseError("Error SetItem format.")

    def exitOC_PropertyExpression(self, ctx: s_cypherParser.OC_PropertyExpressionContext):
        if self.is_set:
            # ===SetPropertyExpression
            # atom: Atom,
            # property_chains: List[str],
            # time_window: AtTElement = None
            atom = self.atom
            self.atom = None  # 退出清空
            property_chains = self.property_look_up_list
            self.property_look_up_list = []  # 退出清空
            time_window = self.at_t_element
            self.at_t_element = None
            self.set_property_expression.push(SetPropertyExpression(atom, property_chains, time_window))
        elif self.is_remove:
            # atom: Atom,
            # property_chains: List[str]
            atom = self.atom
            self.atom = None  # 退出清空
            property_chains = self.property_look_up_list
            self.property_look_up_list = []  # 退出清空
            self.remove_property_expression.push(RemovePropertyExpression(atom, property_chains))

    def enterOC_Remove(self, ctx: s_cypherParser.OC_RemoveContext):
        self.is_remove = True

    def exitOC_Remove(self, ctx: s_cypherParser.OC_RemoveContext):
        # remove_items: List[LabelSetting | RemovePropertyExpression]
        remove_items = self.remove_items
        self.remove_items = []  # 退出清空
        self.remove_clause = RemoveClause(remove_items)
        self.is_remove = False

    def exitOC_RemoveItem(self, ctx: s_cypherParser.OC_RemoveItemContext):
        # item: List[LabelSetting | RemovePropertyExpression]
        # LabelSetting
        #   variable: str,
        #   labels: List[str]
        if ctx.oC_Variable() is not None and ctx.oC_NodeLabels() is not None:
            variable = ctx.oC_Variable().getText()
            labels = self.node_labels
            self.node_labels = []  # 退出清空
            self.remove_items.append(LabelSetting(variable, labels))
        elif ctx.oC_PropertyExpression() is not None:
            self.remove_items.append(self.remove_property_expression.pop())
        else:
            raise ParseError("RemoveItem format error.")

    def exitS_Stale(self, ctx: s_cypherParser.S_StaleContext):
        # stale_items: List[StaleItem]
        # at_time_clause: AtTimeClause = None
        at_time_clause = self.at_time_clause
        self.at_time_clause = None  # 退出清空
        stale_items = self.stale_items
        self.stale_clause = StaleClause(stale_items, at_time_clause)
        self.stale_items = []  # 退出清空

    def exitS_StaleItem(self, ctx: s_cypherParser.S_StaleItemContext):
        # expression: Expression,
        # property_name: str = None,
        # is_value=False
        if self.expression.is_empty() is False:
            expression = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        property_name = None
        if ctx.s_PropertyLookupName() is not None:
            property_name = self.property_look_up_name
            self.property_look_up_name = None
        is_value = False
        if ctx.PoundValue() is not None:
            is_value = True
        self.stale_items.append(StaleItem(expression, property_name, is_value))

    # 时间窗口限定
    def exitS_TimeWindowLimit(self, ctx: s_cypherParser.S_TimeWindowLimitContext):
        # time_window_limit: SnapshotClause | ScopeClause
        if ctx.s_Snapshot() is not None:
            self.time_window_limit_clause = TimeWindowLimitClause(self.snapshot_clause)
        elif ctx.s_Scope() is not None:
            self.time_window_limit_clause = TimeWindowLimitClause(self.scope_clause)

    def exitS_Snapshot(self, ctx: s_cypherParser.S_SnapshotContext):
        # time_point: Expression
        if self.expression.is_empty() is False:
            self.snapshot_clause = SnapshotClause(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def exitS_Scope(self, ctx: s_cypherParser.S_ScopeContext):
        # interval: Expression
        if self.expression.is_empty() is False:
            self.scope_clause = ScopeClause(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def exitOC_Atom(self, ctx: s_cypherParser.OC_AtomContext):
        # atom: str | ListLiteral | MapLiteral | CaseExpression | ListComprehension | PatternComprehension | Quantifier
        # | PatternPredicate | ParenthesizedExpression | FunctionInvocation | ExistentialSubquery
        # BooleanLiteral、NULL、NumberLiteral、StringLiteral、COUNT(*)和Parameter类型可以直接用str存储
        atom = None
        if self.list_literal is not None:
            atom = Atom(self.list_literal)
            self.list_literal = None
        elif self.map_literal is not None:
            atom = Atom(self.map_literal)
            self.map_literal = None
        elif ctx.oC_CaseExpression() is not None:
            # TODO
            atom = Atom(self.case_expression.pop())
        elif ctx.oC_ListComprehension() is not None:
            atom = Atom(self.list_comprehension)
            self.list_comprehension = None
        elif ctx.oC_PatternComprehension() is not None:
            # TODO
            atom = Atom(self.pattern_comprehension)
            self.pattern_comprehension = None
        elif ctx.oC_Quantifier() is not None:
            # TODO
            atom = Atom(self.quantifier)
            self.quantifier = None
        elif ctx.oC_PatternPredicate() is not None:
            # TODO
            atom = Atom(self.pattern_predicate)
            self.pattern_predicate = None
        elif ctx.oC_ParenthesizedExpression() is not None:
            atom = Atom(self.parenthesized_expression.pop())
        elif ctx.oC_FunctionInvocation() is not None:
            atom = Atom(self.function_invocation.pop())
        elif ctx.oC_ExistentialSubquery() is not None:
            # TODO
            atom = Atom(self.existential_subquery)
            self.existential_subquery = None
        elif ctx.oC_Literal() is not None:
            # 处理str类型
            if ctx.oC_Literal().oC_BooleanLiteral() is not None:
                atom = Atom(ctx.oC_Literal().oC_BooleanLiteral().getText())
            elif ctx.oC_Literal().NULL() is not None:
                atom = Atom(ctx.oC_Literal().getText())
            elif ctx.oC_Literal().oC_NumberLiteral() is not None:
                atom = Atom(ctx.oC_Literal().oC_NumberLiteral().getText())
            elif ctx.oC_Literal().StringLiteral() is not None:
                atom = Atom(ctx.oC_Literal().StringLiteral().getText())
        elif ctx.oC_Parameter() is not None:
            atom = Atom(ctx.oC_Parameter().getText())
        elif ctx.COUNT() is not None:
            atom = Atom(ctx.getText())
        else:
            atom = Atom(ctx.getText())
        self.atom = atom

    def exitOC_ListComprehension(self, ctx: s_cypherParser.OC_ListComprehensionContext):
        # variable: str,
        # list_expression,
        # where_expression=None,
        # back_expression=None
        if ctx.oC_FilterExpression().oC_IdInColl().oC_Variable() is not None:
            variable = ctx.oC_FilterExpression().oC_IdInColl().oC_Variable().getText()
        else:
            raise ParseError("The variable of oC_IdInColl is None!")
        if self.list_expression.is_empty() is False:
            list_expression = self.list_expression.pop()
        else:
            list_expression = None
        if self.filter_where_expression.is_empty() is False:
            where_expression = self.filter_where_expression.pop()
        else:
            where_expression = None
        if ctx.oC_Expression() is not None:
            if self.expression.is_empty() is False:
                back_expression = self.expression.pop()
            else:
                raise ParseError("Expect expression but there is none in expression stack.")
        else:
            back_expression = None
        self.list_comprehension = ListComprehension(variable, list_expression, where_expression, back_expression)

    def exitOC_FilterExpression(self, ctx: s_cypherParser.OC_FilterExpressionContext):
        if self.where_expression.is_empty() is False:
            self.filter_where_expression.push(self.where_expression.pop())

    def exitOC_IdInColl(self, ctx: s_cypherParser.OC_IdInCollContext):
        if self.expression.is_empty() is False:
            self.list_expression.push(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def enterOC_ListLiteral(self, ctx: s_cypherParser.OC_ListLiteralContext):
        self.list_literal_expressions.push([])

    def exitOC_ListLiteral(self, ctx: s_cypherParser.OC_ListLiteralContext):
        # expressions: List
        self.list_literal = ListLiteral(self.list_literal_expressions.pop())

    def exitS_ListLiteralExpression(self, ctx: s_cypherParser.S_ListLiteralExpressionContext):
        if self.expression.is_empty() is False:
            self.list_literal_expressions.peek().append(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def exitOC_MapLiteral(self, ctx: s_cypherParser.OC_MapLiteralContext):
        # keys_values: dict
        # key_values为dict[str, Expression]类型
        self.map_literal = MapLiteral(self.map_key_values)
        self.map_key_values = dict()  # 退出清空

    def exitS_MapKeyValue(self, ctx: s_cypherParser.S_MapKeyValueContext):
        # oC_PropertyKeyName SP? ':' SP? oC_Expression SP?
        property_key_name = None
        if ctx.oC_PropertyKeyName() is not None:
            property_key_name = ctx.oC_PropertyKeyName().getText()
        if self.expression.is_empty() is False:
            expression = self.expression.pop()
        else:
            raise ParseError("Expect expression but there is none in expression stack.")
        if property_key_name is not None:
            self.map_key_values[property_key_name] = expression

    def exitOC_ParenthesizedExpression(self, ctx: s_cypherParser.OC_ParenthesizedExpressionContext):
        # expression
        if self.expression.is_empty() is False:
            self.parenthesized_expression.push(ParenthesizedExpression(self.expression.pop()))
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def enterOC_FunctionInvocation(self, ctx: s_cypherParser.OC_FunctionInvocationContext):
        self.function_invocation_expressions.push([])

    def exitOC_FunctionInvocation(self, ctx: s_cypherParser.OC_FunctionInvocationContext):
        # function_name: str,
        # is_distinct=False,
        # expressions: List = None
        function_name = ctx.oC_FunctionName().getText()
        is_distinct = False
        if ctx.DISTINCT() is not None:
            is_distinct = True
        if ctx.s_FunctionInvocationExpression() is not None and len(self.function_invocation_expressions.peek()) > 0:
            expressions = self.function_invocation_expressions.pop()
        else:
            tmp = self.function_invocation_expressions.pop()
            expressions = None
        self.function_invocation.push(FunctionInvocation(function_name, is_distinct, expressions))

    def exitS_FunctionInvocationExpression(self, ctx: s_cypherParser.S_FunctionInvocationExpressionContext):
        if ctx.oC_Expression() is not None and self.expression.is_empty() is False:
            self.function_invocation_expressions.peek().append(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    # expression新方案，使用队列来存储已经遍历过的语法子树信息
    def exitOC_Expression(self, ctx: s_cypherParser.OC_ExpressionContext):
        expression = Expression(self.or_expression.pop())
        self.expression.push(expression)

    def enterOC_OrExpression(self, ctx: s_cypherParser.OC_OrExpressionContext):
        self.xor_expressions.push([])

    def exitOC_OrExpression(self, ctx: s_cypherParser.OC_OrExpressionContext):
        # xor_expressions: List[XorExpression]
        or_expression = OrExpression(self.xor_expressions.pop())
        self.or_expression.push(or_expression)

    def enterOC_XorExpression(self, ctx: s_cypherParser.OC_XorExpressionContext):
        self.and_expressions.push([])

    def exitOC_XorExpression(self, ctx: s_cypherParser.OC_XorExpressionContext):
        # and_expressions: List[AndExpression]
        self.xor_expressions.peek().append(XorExpression(self.and_expressions.pop()))

    def enterOC_AndExpression(self, ctx: s_cypherParser.OC_AndExpressionContext):
        self.not_expressions.push([])

    def exitOC_AndExpression(self, ctx: s_cypherParser.OC_AndExpressionContext):
        # not_expressions: List[NotExpression]
        self.and_expressions.peek().append(AndExpression(self.not_expressions.pop()))

    def exitOC_NotExpression(self, ctx: s_cypherParser.OC_NotExpressionContext):
        # comparison_expression: ComparisonExpression,
        # is_not=False
        is_not = False
        if ctx.NOT():
            is_not = True
        if ctx.oC_ComparisonExpression() is not None:
            self.not_expressions.peek().append(NotExpression(self.comparison_expression.pop(), is_not))
        else:
            raise ParseError("ComparisonExpression is expected but there is none.")

    def enterOC_ComparisonExpression(self, ctx: s_cypherParser.OC_ComparisonExpressionContext):
        self.subject_expressions.push([])
        self.comparison_operations.push([])

    def exitOC_ComparisonExpression(self, ctx: s_cypherParser.OC_ComparisonExpressionContext):
        # subject_expressions: List[SubjectExpression],
        # comparison_operations: List[str] = None
        # 第一个SubjectExpression不可少，后面每一个符号和一个SubjectExpression为一组合
        # 获取比较运算符
        if len(self.comparison_operations.peek()) == 0:
            cmp_op = self.comparison_operations.pop()
            comparison_operations = None
        else:
            comparison_operations = self.comparison_operations.pop()
        # 比较运算符的个数=元素个数+1
        # TODO empty
        if len(self.subject_expressions.peek()) > 0:
            subject_expressions = self.subject_expressions.pop()
        else:
            raise ParseError("At least one SubjectExpression is expected but there is none.")
        self.comparison_expression.push(ComparisonExpression(subject_expressions, comparison_operations))

    def exitS_ComparisonOperator(self, ctx: s_cypherParser.S_ComparisonOperatorContext):
        self.comparison_operations.peek().append(ctx.getText())

    def exitOC_StringListNullPredicateExpression(self, ctx: s_cypherParser.OC_StringListNullPredicateExpressionContext):
        # add_or_subtract_expression: AddSubtractExpression,
        # predicate_expression: TimePredicateExpression | StringPredicateExpression
        # | ListPredicateExpression | NullPredicateExpression = None
        if ctx.oC_AddOrSubtractExpression() is not None and self.add_subtract_expression.is_empty() is False:
            add_or_subtract_expression = self.add_subtract_expression.pop()
        else:
            raise ParseError("At least one AddOrSubtractExpression is expected but there is none.")
        predicate_expression = None
        if ctx.s_TimePredicateExpression() is not None:
            predicate_expression = self.time_predicate_expression.pop()
        elif ctx.oC_StringPredicateExpression() is not None:
            predicate_expression = self.string_predicate_expression.pop()
        elif ctx.oC_ListPredicateExpression() is not None:
            predicate_expression = self.list_predicate_expression.pop()
        elif ctx.oC_NullPredicateExpression() is not None:
            predicate_expression = self.null_predicate_expression.pop()
        self.subject_expressions.peek().append(SubjectExpression(add_or_subtract_expression, predicate_expression))

    def exitS_TimePredicateExpression(self, ctx: s_cypherParser.S_TimePredicateExpressionContext):
        # time_operation: str,
        # add_or_subtract_expression: AddSubtractExpression
        time_str = ctx.getText()
        # 检查ctx.
        if 'DURING' in time_str and 'OVERLAPS' not in time_str:
            time_operation = 'DURING'
        elif 'DURING' not in time_str and 'OVERLAPS' in time_str:
            time_operation = 'OVERLAPS'
        else:
            raise ParseError("The time predicate expression must have the operation DURING or OVERLAPS.")
        if ctx.oC_AddOrSubtractExpression() is not None and self.add_subtract_expression.is_empty() is False:
            add_or_subtract_expression = self.add_subtract_expression.pop()
        else:
            raise ParseError("At least one AddOrSubtractExpression is expected but there is none.")
        self.time_predicate_expression.push(TimePredicateExpression(time_operation, add_or_subtract_expression))

    def exitOC_StringPredicateExpression(self, ctx: s_cypherParser.OC_StringPredicateExpressionContext):
        # string_operation: str,
        # add_or_subtract_expression: AddSubtractExpression
        string_str = ctx.getText()
        if ctx.STARTS() is not None and ctx.WITH() is not None:
            string_operation = 'STARTS WITH'
        elif ctx.ENDS() and ctx.WITH() is not None:
            string_operation = 'ENDS WITH'
        elif ctx.CONTAINS() is not None:
            string_operation = 'CONTAINS'
        else:
            raise ParseError("There must have an operation among 'STARTS WITH','ENDS WITH' and 'CONTAINS'.")
        if ctx.oC_AddOrSubtractExpression() is not None and self.add_subtract_expression.is_empty() is False:
            add_or_subtract_expression = self.add_subtract_expression.pop()
        else:
            raise ParseError("At least one AddOrSubtractExpression is expected but there is none.")
        self.string_predicate_expression.push(StringPredicateExpression(string_operation, add_or_subtract_expression))

    def exitOC_ListPredicateExpression(self, ctx: s_cypherParser.OC_ListPredicateExpressionContext):
        # add_or_subtract_expression: AddSubtractExpression
        if ctx.oC_AddOrSubtractExpression() is not None and self.add_subtract_expression.is_empty() is False:
            add_or_subtract_expression = self.add_subtract_expression.pop()
            self.list_predicate_expression.push(ListPredicateExpression(add_or_subtract_expression))
        else:
            raise ParseError("At least one AddOrSubtractExpression is expected but there is none.")

    def exitOC_NullPredicateExpression(self, ctx: s_cypherParser.OC_NullPredicateExpressionContext):
        # is_null: bool = True
        if ctx.IS() is not None and ctx.NOT() is not None and ctx.NULL() is not None:
            is_null = False
        else:
            is_null = True
        self.null_predicate_expression.push(NullPredicateExpression(is_null))

    def enterOC_AddOrSubtractExpression(self, ctx: s_cypherParser.OC_AddOrSubtractExpressionContext):
        self.multiply_divide_modulo_expressions.push([])
        self.add_subtract_operations.push([])

    def exitOC_AddOrSubtractExpression(self, ctx: s_cypherParser.OC_AddOrSubtractExpressionContext):
        # multiply_divide_modulo_expressions: List[MultiplyDivideExpression],
        # add_subtract_operations: List[str] = None
        # 获取加减运算符
        if len(self.add_subtract_operations.peek()) > 0:
            add_subtract_operations = self.add_subtract_operations.pop()
        else:
            as_op = self.add_subtract_operations.pop()
            add_subtract_operations = None
        # TODO empty
        if ctx.oC_MultiplyDivideModuloExpression() is not None and len(self.multiply_divide_modulo_expressions.peek()) > 0:
            multiply_divide_modulo_expressions = self.multiply_divide_modulo_expressions.pop()
        else:
            raise ParseError("At least one MultiplyDivideExpression is expected but there is none.")
        self.add_subtract_expression.push(AddSubtractExpression(multiply_divide_modulo_expressions,
                                                               add_subtract_operations))

    def exitS_AddOrSubtractOperator(self, ctx: s_cypherParser.S_AddOrSubtractOperatorContext):
        self.add_subtract_operations.peek().append(ctx.getText())

    def enterOC_MultiplyDivideModuloExpression(self, ctx: s_cypherParser.OC_MultiplyDivideModuloExpressionContext):
        self.power_expressions.push([])
        self.multiply_divide_module_operations.push([])

    def exitOC_MultiplyDivideModuloExpression(self, ctx: s_cypherParser.OC_MultiplyDivideModuloExpressionContext):
        # power_expressions: List[PowerExpression],
        # multiply_divide_operations: List[str] = None
        # 获取乘除模运算符
        if len(self.multiply_divide_module_operations.peek()) > 0:
            multiply_divide_operations = self.multiply_divide_module_operations.pop()
        else:
            md_op = self.multiply_divide_module_operations.pop()
            multiply_divide_operations = None
        if ctx.oC_PowerOfExpression() is not None and len(self.power_expressions.peek()) > 0:
            power_expressions = self.power_expressions.pop()
        else:
            raise ParseError("At least one PowerExpression is expected but there is none.")
        self.multiply_divide_modulo_expressions.peek().append(
            MultiplyDivideModuloExpression(power_expressions, multiply_divide_operations))

    def exitS_MultiplyDivideModuloOperator(self, ctx: s_cypherParser.S_MultiplyDivideModuloOperatorContext):
        self.multiply_divide_module_operations.peek().append(ctx.getText())

    def enterOC_PowerOfExpression(self, ctx: s_cypherParser.OC_PowerOfExpressionContext):
        self.list_index_expressions.push([])

    def exitOC_PowerOfExpression(self, ctx: s_cypherParser.OC_PowerOfExpressionContext):
        # list_index_expressions: List[ListIndexExpression]
        self.power_expressions.peek().append(PowerExpression(self.list_index_expressions.pop()))

    def exitOC_ListOperatorExpression(self, ctx: s_cypherParser.OC_ListOperatorExpressionContext):
        if ctx.oC_PropertyOrLabelsExpression() is not None:
            self.principal_expression.push(self.properties_labels_expression.pop())
        elif ctx.s_AtTExpression() is not None:
            self.principal_expression.push(self.AtT_expression.pop())
        else:
            raise ParseError("At least one PropertyOrLabelsExpression or AtTExpression is expected but there is none.")

    def enterOC_UnaryAddOrSubtractExpression(self, ctx: s_cypherParser.OC_UnaryAddOrSubtractExpressionContext):
        self.index_expressions.push([])

    def exitOC_UnaryAddOrSubtractExpression(self, ctx: s_cypherParser.OC_UnaryAddOrSubtractExpressionContext):
        # 最后要返回的ListIndexExpression的参数如下
        # principal_expression: PropertiesLabelsExpression | AtTExpression,
        # is_positive=True,
        # index_expressions: List[IndexExpression] = None
        is_positive = True
        if ctx.getText()[0] == '-':
            is_positive = False
        principal_expression = self.principal_expression.pop()
        # TODO empty
        if len(self.index_expressions.peek()) > 0:
            index_expressions = self.index_expressions.pop()
        else:
            tmp = self.index_expressions.pop()
            index_expressions = None
        self.list_index_expressions.peek().append(ListIndexExpression(principal_expression, is_positive,
                                                                        index_expressions))

    # 获取单个的IndexExpression
    def exitS_SingleIndexExpression(self, ctx: s_cypherParser.S_SingleIndexExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = self.left_expression.pop()
        index_expression = IndexExpression(left_expression, None)
        self.index_expressions.peek().append(index_expression)

    # 获取成对的IndexExpression
    def exitS_DoubleIndexExpression(self, ctx: s_cypherParser.S_DoubleIndexExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = self.left_expression.pop()
        right_expression = self.right_expression.pop()
        index_expression = IndexExpression(left_expression, right_expression)
        self.index_expressions.peek().append(index_expression)

    def exitS_LeftExpression(self, ctx: s_cypherParser.S_LeftExpressionContext):
        if self.expression.is_empty() is False:
            self.left_expression.push(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def exitS_RightExpression(self, ctx: s_cypherParser.S_RightExpressionContext):
        if self.expression.is_empty() is False:
            self.right_expression.push(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    def exitOC_PropertyOrLabelsExpression(self, ctx: s_cypherParser.OC_PropertyOrLabelsExpressionContext):
        # atom: Atom,
        # property_chains: List[str] = None,
        # labels_or_at_t: List[str] | AtTElement = None
        atom = self.atom
        self.atom = None
        if ctx.oC_PropertyLookup() is not None:
            property_chains = self.property_look_up_list
            self.property_look_up_list = []  # 退出清空
        else:
            property_chains = None
        if ctx.oC_NodeLabels() is not None:
            labels_or_at_t = self.node_labels
            self.node_labels = []  # 退出清空
        elif ctx.s_AtTElement() is not None:
            labels_or_at_t = self.at_t_element
            self.at_t_element = None
        else:
            labels_or_at_t = None
        self.properties_labels_expression.push(PropertiesLabelsExpression(atom, property_chains, labels_or_at_t))

    def exitS_AtTExpression(self, ctx: s_cypherParser.S_AtTExpressionContext):
        # atom: Atom,
        # property_chains: List[str] = None,
        # property_name: str = None,
        # time_window: bool | AtTElement = None,
        # time_property_chains: List[str] = None
        atom = self.atom
        self.atom = None
        # 获取属性
        if len(self.property_look_up_list) == 0:
            property_chains = None
        else:
            property_chains = self.property_look_up_list
            self.property_look_up_list = []
        # 获取属性名
        property_name = self.property_look_up_name
        self.property_look_up_name = None
        # 获取时间窗口
        if ctx.s_AtTElement() is not None:
            time_window = self.at_t_element
            self.at_t_element = None
        elif ctx.PoundValue() is not None:
            time_window = True
        else:
            time_window = None
        # 获取时间属性
        if ctx.s_PropertyLookupTime() is not None:
            time_property_chains = self.property_look_up_time_list
            self.property_look_up_time_list = []  # 退出清空
        else:
            time_property_chains = None
        self.AtT_expression.push(AtTExpression(atom, property_chains, property_name, time_window, time_property_chains))

    def exitS_PropertyLookupName(self, ctx: s_cypherParser.S_PropertyLookupNameContext):
        self.property_look_up_name = ctx.oC_PropertyKeyName().getText()

    def exitOC_Where(self, ctx: s_cypherParser.OC_WhereContext):
        if self.expression.is_empty() is False:
            self.where_expression.push(self.expression.pop())
        else:
            raise ParseError("Expect expression but there is none in expression stack.")

    # # 打印遍历语法树过程
    # def enterEveryRule(self, ctx):
    #     print("Enter rule:", type(ctx).__name__)
    #     print("  Text:", ctx.getText())
    #
    # def exitEveryRule(self, ctx):
    #     print("Exit rule:", type(ctx).__name__)
    #     print("  Text:", ctx.getText())


class Stack(object):
    def __init__(self):  # 初始化栈为空列表
        self.items = []

    def is_empty(self):  # 判断栈是否为空
        return self.items == []

    def peek(self):  # 返回栈顶元素
        if self.items:
            return self.items[len(self.items) - 1]
        else:
            raise IndexError("从空栈执行弹出栈顶元素操作")

    def peek_is_empty(self):
        if self.items:
            return self.peek() == []
        else:
            return self.items == []

    def size(self):  # 返回栈的大小
        return len(self.items)

    def push(self, item):  # 新元素（入栈）
        self.items.append(item)

    def pop(self):  # 删除栈顶元素（出栈）
        if self.items:
            return self.items.pop()
        else:
            raise IndexError("从空栈执行出栈操作")
