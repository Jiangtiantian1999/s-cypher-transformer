from transformer.grammar_parser.s_cypherListener import s_cypherListener
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *
from transformer.ir.s_expression import *
from transformer.exceptions.s_exception import *


# This class records important information about the query
class SCypherWalker(s_cypherListener):
    def __init__(self, parser: s_cypherParser):
        self.parser = parser

        # node
        self.properties = dict()  # 对象节点的属性 dict[PropertyNode, ValueNode]
        self.property_node_list = []  # 属性节点列表
        self.value_node_list = []  # 值节点列表
        self.node_labels = []

        # time
        self.at_time_clause = None
        self.at_t_element = None
        self.time_point_literals = []
        self.map_literal = None

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

        # clauses
        self.query_clause = None
        self.single_query_clauses = []
        self.multi_part_query_clauses = []
        self.single_part_query_clause = None
        self.union_query_clause = None
        self.with_clause = None
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
        self.skip_expression = None  # Expression类型
        self.limit_expression = None
        self.expression = None
        self.or_expression = None
        self.xor_expressions = []
        self.and_expressions = []
        self.not_expressions = []
        self.comparison_expression = None
        self.subject_expressions = []
        self.null_predicate_expression = None
        self.list_predicate_expression = None
        self.string_predicate_expression = None
        self.time_predicate_expression = None
        self.add_subtract_expressions = []  # 第一个是oC_StringListNullPredicateExpression里的，第二个是PredicateExpression里的
        self.multiply_divide_expressions = []
        self.power_expressions = []
        self.list_index_expressions = []
        self.index_expressions = []
        self.AtT_expression = None
        self.properties_labels_expression = None

        # where expression
        self.where_skip_expression = None  # Expression类型
        self.where_limit_expression = None
        self.where_expression = None
        self.where_or_expression = None
        self.where_xor_expressions = []
        self.where_and_expressions = []
        self.where_not_expressions = []
        self.where_comparison_expression = None
        self.where_subject_expressions = []
        self.where_null_predicate_expression = None
        self.where_list_predicate_expression = None
        self.where_string_predicate_expression = None
        self.where_time_predicate_expression = None
        self.where_add_subtract_expressions = []
        self.where_multiply_divide_expressions = []
        self.where_power_expressions = []
        self.where_list_index_expressions = []
        self.where_index_expressions = []
        self.where_AtT_expression = None
        self.where_properties_labels_expression = None

        # 中间变量
        self.with_query_clauses = []
        self.union_is_all_list = []
        self.projection_items = []
        self.property_look_up_list = []
        self.property_look_up_time_list = []
        self.sort_items = dict()
        self.yield_items = []
        self.procedure_name = None
        self.explicit_input_items = []  # 带参程序调用
        self.implicit_input_items = None  # 不带参程序调用
        self.left_index_expression = None
        self.delete_items = []
        self.merge_actions = dict()
        self.set_items = []
        self.remove_items = []
        self.stale_items = []
        self.operations = []
        self.left_expression = None
        self.right_expression = None
        self.map_key_values = dict()
        self.integer_literals = []

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
            if "UNION ALL" in ctx.UNION().getText():
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
        self.with_query_clauses.append(WithQueryClause(with_clause, reading_clauses, updating_clauses))

    def exitOC_UpdatingClause(self, ctx: s_cypherParser.OC_UpdatingClauseContext):
        # update_clause: CreateClause | DeleteClause | StaleClause | SetClause | MergeClause | RemoveClause,
        # at_time_clause: AtTimeClause = None
        update_clause = None
        if ctx.oC_Create() is not None:
            update_clause = self.create_clause
        elif ctx.oC_Merge() is not None:
            update_clause = self.merge_clause
        elif ctx.oC_Delete() is not None:
            update_clause = self.delete_clause
        elif ctx.oC_Set() is not None:
            update_clause = self.set_clause
        elif ctx.oC_Remove() is not None:
            update_clause = self.remove_clause
        elif ctx.s_Stale() is not None:
            update_clause = self.stale_clause
        self.updating_clauses.append(UpdatingClause(update_clause, self.at_time_clause))

    def exitOC_MultiPartQuery(self, ctx: s_cypherParser.OC_MultiPartQueryContext):
        # single_query_clause: SingleQueryClause = None,
        # with_query_clauses: List[WithQueryClause] = None
        self.multi_part_query_clauses.append(MultiQueryClause(self.single_part_query_clause, self.with_query_clauses))
        self.with_query_clauses = []  # 退出清空

    # SinglePartQuery或者MultiPartQuery
    def exitOC_SingleQuery(self, ctx: s_cypherParser.OC_SingleQueryContext):
        if len(self.multi_part_query_clauses) > 0:
            # self.single_query_clauses.append(self.multi_part_query_clauses)
            self.single_query_clauses = self.multi_part_query_clauses
        else:
            self.single_query_clauses.append(MultiQueryClause(self.single_part_query_clause, None))
        self.multi_part_query_clauses = []  # 退出清空

    def exitOC_SinglePartQuery(self, ctx: s_cypherParser.OC_SinglePartQueryContext):
        # reading_clauses: List[ReadingClause] = None,
        # updating_clauses: List[UpdatingClause] = None,
        # return_clause: ReadingClause
        self.single_part_query_clause = SingleQueryClause(self.reading_clauses, self.updating_clauses,
                                                          self.return_clause)
        self.reading_clauses = []  # 退出清空
        self.updating_clauses = []

    def exitOC_With(self, ctx: s_cypherParser.OC_WithContext):
        # projection_items: List[ProjectionItem],
        # is_distinct: bool = False,
        # order_by_clause: OrderByClause = None,
        # skip_expression: Expression = None,
        # limit_expression: Expression = None
        projection_items = self.projection_items
        self.projection_items = []  # 退出清空
        is_distinct = False
        if 'DISTINCT' in ctx.oC_ProjectionBody().getText():
            is_distinct = True
        order_by_clause = self.order_by_clause
        skip_expression = self.skip_expression
        limit_expression = self.limit_expression
        self.with_clause = WithClause(projection_items, is_distinct, order_by_clause, skip_expression, limit_expression)

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
        elif ctx.s_Between() is not None:
            time_window = self.between_clause
        if ctx.s_Where() is not None:
            where_expression = self.where_expression
        self.match_clause = MatchClause(patterns, is_optional, where_expression, time_window)

    def exitS_Between(self, ctx: s_cypherParser.S_BetweenContext):
        # interval: Expression
        # interval = ctx.oC_Expression().getText()
        interval = self.expression
        self.between_clause = BetweenClause(interval)

    def exitS_AtTime(self, ctx: s_cypherParser.S_AtTimeContext):
        self.at_time_clause = AtTimeClause(self.expression)

    def exitOC_Unwind(self, ctx: s_cypherParser.OC_UnwindContext):
        # expression: Expression,
        # variable: str
        expression = self.expression
        variable = ctx.oC_Variable().getText()
        self.unwind_clause = UnwindClause(expression, variable)

    def exitOC_InQueryCall(self, ctx: s_cypherParser.OC_InQueryCallContext):
        # procedure_name: str,
        # input_items: List[Expression] = None,
        # yield_clause: YieldClause = None
        self.in_query_call_clause = CallClause(self.procedure_name, self.explicit_input_items, self.yield_clause)
        self.explicit_input_items = []  # 退出清空

    def enterOC_ProcedureName(self, ctx: s_cypherParser.OC_ProcedureNameContext):
        self.procedure_name = ctx.getText()

    def exitOC_YieldItems(self, ctx: s_cypherParser.OC_YieldItemsContext):
        # yield_items: List[YieldItem],
        # where_expression: Expression = None
        self.yield_clause = YieldClause(self.yield_items, self.where_expression)
        self.yield_items = []  # 退出清空

    def exitOC_YieldItem(self, ctx: s_cypherParser.OC_YieldItemContext):
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
        input_items = None
        if ctx.oC_ExplicitProcedureInvocation() is not None:
            input_items = self.explicit_input_items
            self.explicit_input_items = []  # 退出清空
        elif ctx.oC_ImplicitProcedureInvocation() is not None:
            input_items = self.implicit_input_items
        self.stand_alone_call_clause = CallClause(self.procedure_name, input_items, self.yield_clause)

    @staticmethod
    def getAtTElement(interval_str) -> AtTElement:
        index = 0
        interval_from = interval_to = ""
        find_from = find_to = False
        while index < len(interval_str):
            if interval_str[index] == " ":
                index = index + 1
                continue
            elif interval_str[index] == '(':
                find_from = True
            elif interval_str[index] == ',':
                find_to = True
                find_from = False
            elif interval_str[index] == ')':
                break
            elif find_from:
                interval_from += interval_str[index]
            elif find_to:
                interval_to += interval_str[index]
            index = index + 1
        if interval_to == "NOW":
            at_t_element = AtTElement(TimePointLiteral(interval_from.strip('"')), TimePointLiteral("NOW"))
        else:
            at_t_element = AtTElement(TimePointLiteral(interval_from.strip('"')),
                                      TimePointLiteral(interval_to.strip('"')))
        return at_t_element

    # 获取对象节点
    def exitOC_NodePattern(self, ctx: s_cypherParser.OC_NodePatternContext):
        # node_content = ""  # 对象节点内容
        node_label_list = self.node_labels  # 对象节点标签
        self.node_labels = []  # 退出清空
        interval = None  # 对象节点时间
        properties = dict()  # 对象节点属性
        variable = None
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        if ctx.s_AtTElement() is not None:
            n_interval = ctx.s_AtTElement()
            interval_str = n_interval.getText()
            interval = self.getAtTElement(interval_str)
        if ctx.s_Properties() is not None:
            properties = self.properties
        self.properties = dict()  # 退出清空
        self.object_node_list.append(ObjectNode(node_label_list, variable, interval, properties))

    def exitOC_NodeLabel(self, ctx: s_cypherParser.OC_NodeLabelContext):
        self.node_labels.append(ctx.getText().strip(':'))

    def exitS_PropertiesPattern(self, ctx: s_cypherParser.S_PropertiesPatternContext):
        # 将属性节点和值节点组合成对象节点的属性
        for prop_node, val_node in zip(self.property_node_list, self.value_node_list):
            self.properties[prop_node] = val_node
        # 退出清空
        self.property_node_list = []
        self.value_node_list = []

    # 获取属性节点
    def exitS_PropertyNode(self, ctx: s_cypherParser.S_PropertyNodeContext):
        # 获取属性节点内容
        property_content = ctx.oC_PropertyKeyName().getText()  # 属性节点内容
        # 获取属性节点的时间
        property_interval = self.at_t_element  # 属性节点时间
        self.property_node_list.append(PropertyNode(property_content, None, property_interval))

    def exitS_ValueNode(self, ctx: s_cypherParser.S_ValueNodeContext):
        value_content = None  # 值节点内容
        value_interval = None  # 值节点时间
        # 获取值节点内容
        if ctx.oC_Expression() is not None:
            value_content = self.expression
        # 获取值节点的时间
        if ctx.s_AtTElement() is not None:
            value_interval = self.at_t_element
        # 构造值节点
        self.value_node_list.append(ValueNode(value_content, None, value_interval))

    # 获取时间
    def exitS_AtTElement(self, ctx: s_cypherParser.S_AtTElementContext):
        if len(self.time_point_literals) == 2:
            self.at_t_element = AtTElement(self.time_point_literals[0], self.time_point_literals[1])
        elif len(self.time_point_literals) == 1 and ctx.NOW() is not None:
            self.at_t_element = AtTElement(self.time_point_literals[0], TimePointLiteral(ctx.NOW().getText().strip('"')))
        else:
            raise FormatError("Invalid time format!")
        self.time_point_literals = []  # 退出清空

    def exitS_TimePointLiteral(self, ctx: s_cypherParser.S_TimePointLiteralContext):
        if self.map_literal is not None:
            self.time_point_literals.append(TimePointLiteral(self.map_literal))
        else:
            self.time_point_literals.append(TimePointLiteral(ctx.StringLiteral().getText().strip('"')))

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
        expression = self.expression
        if property_key_name is not None:
            self.map_key_values[property_key_name] = expression

    def exitOC_RelationshipDetail(self, ctx: s_cypherParser.OC_RelationshipDetailContext):
        variable = None
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        interval = self.at_t_element
        if ctx.oC_RangeLiteral() is not None:
            length_tuple = self.rel_length_range
            self.rel_length_range = None  # 退出清空
        else:
            length_tuple = (1, 1)
        labels = self.rel_type_names
        self.rel_type_names = []  # 退出清空
        properties = self.properties
        self.properties = dict()  # 退出清空
        self.relationship_pattern = SEdge('UNDIRECTED', variable, labels, length_tuple, interval, properties)

    def exitOC_RangeLiteral(self, ctx: s_cypherParser.OC_RangeLiteralContext):
        length_tuple = tuple()
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
            self.edge_list.append(SEdge(direction))

    def exitS_PathFunctionPattern(self, ctx: s_cypherParser.S_PathFunctionPatternContext):
        # variable: str,
        # function_name: str,
        # path: SPath
        function_name = ctx.oC_FunctionName().getText()
        path = SPath(self.object_node_list, self.edge_list, None)
        self.path_function_pattern = TemporalPathCall("", function_name, path)

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
        if self.path_function_pattern is not None:
            if self.path_function_pattern.__class__ == TemporalPathCall:
                self.path_function_pattern.variable = ctx.oC_Variable().getText()
            pattern = Pattern(self.path_function_pattern)
        else:
            pattern = Pattern(self.pattern_element)
        self.patterns.append(pattern)
        self.object_node_list = []
        self.edge_list = []  # 退出前清空

    def exitOC_Return(self, ctx: s_cypherParser.OC_ReturnContext):
        # projection_items: List[ProjectionItem],
        # is_distinct: bool = False,
        # order_by_clause: OrderByClause = None,
        # skip_expression: Expression = None,
        # limit_expression: Expression = None
        projection_items = self.projection_items
        self.projection_items = []  # 退出清空
        is_distinct = False
        if ctx.oC_ProjectionBody() and ctx.oC_ProjectionBody().DISTINCT() is not None:
            is_distinct = True
        order_by_clause = self.order_by_clause
        skip_expression = self.skip_expression
        limit_expression = self.limit_expression
        self.return_clause = ReturnClause(projection_items, is_distinct, order_by_clause, skip_expression,
                                          limit_expression)

    def exitOC_ProjectionItem(self, ctx: s_cypherParser.OC_ProjectionItemContext):
        # is_all: bool = False,
        # expression: Exception = None,
        # variable: str = None
        is_all = False
        if '*' in ctx.getText():
            is_all = True
        variable = None
        expression = self.expression
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        self.projection_items.append(ProjectionItem(is_all, expression, variable))

    def exitOC_Order(self, ctx: s_cypherParser.OC_OrderContext):
        # sort_items: dict[Expression, str]
        self.order_by_clause = OrderByClause(self.sort_items)
        self.sort_items = dict()  # 退出清空

    def exitOC_SortItem(self, ctx: s_cypherParser.OC_SortItemContext):
        # expression = Expression(ctx.oC_Expression().getText())
        expression = self.expression
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
        # self.skip_expression = Expression(ctx.oC_Expression().getText())  # 暂以字符串的的形式存储
        self.skip_expression = self.expression

    def exitOC_Limit(self, ctx: s_cypherParser.OC_LimitContext):
        # self.limit_expression = Expression(ctx.oC_Expression().getText())  # 暂以字符串的的形式存储
        self.limit_expression = self.expression

    def exitOC_Expression(self, ctx: s_cypherParser.OC_ExpressionContext):
        self.expression = Expression(self.or_expression)
        self.explicit_input_items.append(self.expression)

    def exitOC_OrExpression(self, ctx: s_cypherParser.OC_OrExpressionContext):
        # xor_expressions: List[XorExpression]
        self.or_expression = OrExpression(self.xor_expressions)
        self.xor_expressions = []  # 退出时清空，避免重复记录

    def exitOC_XorExpression(self, ctx: s_cypherParser.OC_XorExpressionContext):
        # and_expressions: List[AndExpression]
        self.xor_expressions.append(XorExpression(self.and_expressions))
        self.and_expressions = []  # 退出时清空，避免重复记录

    def exitOC_AndExpression(self, ctx: s_cypherParser.OC_AndExpressionContext):
        # not_expressions: List[NotExpression]
        self.and_expressions.append(AndExpression(self.not_expressions))
        self.not_expressions = []  # 退出时清空，避免重复记录

    def exitOC_NotExpression(self, ctx: s_cypherParser.OC_NotExpressionContext):
        # comparison_expression: ComparisonExpression,
        # is_not=False
        is_not = False
        if ctx.NOT():
            is_not = True
        self.not_expressions.append(NotExpression(self.comparison_expression, is_not))

    # 语法树获取运算符
    def exitS_operator(self, ctx: s_cypherParser.S_operatorContext):
        self.operations.append(ctx.getText())

    def exitOC_ComparisonExpression(self, ctx: s_cypherParser.OC_ComparisonExpressionContext):
        # subject_expressions: List[SubjectExpression],
        # comparison_operations: List[str] = None
        # 第一个SubjectExpression不可少，后面每一个符号和一个SubjectExpression为一组合
        # 获取比较运算符
        comparison_operations = self.operations
        self.operations = []  # 退出清空
        subject_expressions = self.subject_expressions
        self.subject_expressions = []  # 退出时清空，避免重复记录
        self.comparison_expression = ComparisonExpression(subject_expressions, comparison_operations)

    # 处理subject_expression
    def exitOC_StringListNullPredicateExpression(self, ctx: s_cypherParser.OC_StringListNullPredicateExpressionContext):
        # add_or_subtract_expression: AddSubtractExpression,
        # predicate_expression: TimePredicateExpression | StringPredicateExpression | ListPredicateExpression | NullPredicateExpression = None
        if len(self.add_subtract_expressions) > 0:
            add_or_subtract_expression = self.add_subtract_expressions[0]
            self.add_subtract_expressions = []  # 退出清空
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")
        predicate_expression = None
        if self.time_predicate_expression is not None:
            predicate_expression = self.time_predicate_expression
            self.time_predicate_expression = None
        elif self.string_predicate_expression is not None:
            predicate_expression = self.string_predicate_expression
            self.string_predicate_expression = None
        elif self.list_predicate_expression is not None:
            predicate_expression = self.list_predicate_expression
            self.list_predicate_expression = None
        elif self.null_predicate_expression is not None:
            predicate_expression = self.null_predicate_expression
            self.null_predicate_expression = None
        self.subject_expressions.append(SubjectExpression(add_or_subtract_expression, predicate_expression))

    def exitS_TimePredicateExpression(self, ctx: s_cypherParser.S_TimePredicateExpressionContext):
        # time_operation: str,
        # add_or_subtract_expression: AddSubtractExpression = None
        time_str = ctx.getText()
        if 'DURING' in time_str and 'OVERLAPS' not in time_str:
            time_operation = 'DURING'
        elif 'DURING' not in time_str and 'OVERLAPS' in time_str:
            time_operation = 'OVERLAPS'
        else:
            raise FormatError("The time predicate expression must have the operation DURING or OVERLAPS.")
        if len(self.add_subtract_expressions) == 2:
            add_or_subtract_expression = self.add_subtract_expressions[1]
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")
        self.time_predicate_expression = TimePredicateExpression(time_operation, add_or_subtract_expression)

    def exitOC_StringPredicateExpression(self, ctx: s_cypherParser.OC_StringPredicateExpressionContext):
        # string_operation: str,
        # add_or_subtract_expression: AddSubtractExpression = None
        string_str = ctx.getText()
        if 'STARTS' and 'WITH' in string_str:
            string_operation = 'STARTS WITH'
        elif 'ENDS' and 'WITH' in string_str:
            string_operation = 'ENDS WITH'
        elif 'CONTAINS' in string_str:
            string_operation = 'CONTAINS'
        else:
            raise FormatError("There must have an operation among 'STARTS WITH','ENDS WITH' and 'CONTAINS'.")
        if len(self.add_subtract_expressions) == 2:
            add_or_subtract_expression = self.add_subtract_expressions[1]
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")
        self.string_predicate_expression = StringPredicateExpression(string_operation, add_or_subtract_expression)

    def exitOC_ListPredicateExpression(self, ctx: s_cypherParser.OC_ListPredicateExpressionContext):
        # add_or_subtract_expression: AddSubtractExpression = None
        if len(self.add_subtract_expressions) == 2:
            self.list_predicate_expression = ListPredicateExpression(self.add_subtract_expressions[1])
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")

    def enterOC_NullPredicateExpression(self, ctx: s_cypherParser.OC_NullPredicateExpressionContext):
        is_null = True
        if ctx.IS() and ctx.NOT() and ctx.NULL() is not None:
            is_null = False
        self.null_predicate_expression = NullPredicateExpression(is_null)

    def exitOC_AddOrSubtractExpression(self, ctx: s_cypherParser.OC_AddOrSubtractExpressionContext):
        # multiply_divide_expressions: List[MultiplyDivideExpression],
        # add_subtract_operations: List[str] = None
        # 获取加减运算符
        new_operations_list = self.operations
        self.operations = []  # 退出时清空
        # 暂时解决Atom运算符不匹配问题
        if '(' or ')' in ctx.getText():
            new_operations_list = []
        add_subtract_operations = None
        if len(new_operations_list) > 0:
            add_subtract_operations = new_operations_list
        multiply_divide_expressions = self.multiply_divide_expressions
        self.multiply_divide_expressions = []  # 退出时清空，避免重复记录
        self.add_subtract_expressions.append(
            AddSubtractExpression(multiply_divide_expressions, add_subtract_operations))

    def exitOC_MultiplyDivideModuloExpression(self, ctx: s_cypherParser.OC_MultiplyDivideModuloExpressionContext):
        # power_expressions: List[PowerExpression],
        # multiply_divide_operations: List[str] = None
        # 获取乘除模运算符
        new_operations_list = self.operations
        self.operations = []  # 退出时清空
        if '(' or ')' in ctx.getText():
            new_operations_list = []
        multiply_divide_operations = None
        if len(new_operations_list) > 0:
            multiply_divide_operations = new_operations_list
        power_expressions = self.power_expressions
        self.power_expressions = []  # 退出时清空，避免重复记录
        self.multiply_divide_expressions.append(MultiplyDivideExpression(power_expressions, multiply_divide_operations))

    def exitOC_PowerOfExpression(self, ctx: s_cypherParser.OC_PowerOfExpressionContext):
        # list_index_expressions: List[ListIndexExpression]
        new_power_expression = PowerExpression(self.list_index_expressions)
        self.power_expressions.append(new_power_expression)
        self.list_index_expressions = []  # 退出时清空，避免重复记录

    def exitOC_UnaryAddOrSubtractExpression(self, ctx: s_cypherParser.OC_UnaryAddOrSubtractExpressionContext):
        # 最后要返回的ListIndexExpression的参数如下
        # principal_expression: PropertiesLabelsExpression | AtTExpression,
        # is_positive=True,
        # index_expressions: List[IndexExpression] = None
        is_positive = True
        if '-' in ctx.getText():
            is_positive = False
        principal_expression = None
        if self.properties_labels_expression is not None:
            principal_expression = self.properties_labels_expression
            self.properties_labels_expression = None
        elif self.AtT_expression is not None:
            principal_expression = self.AtT_expression
            self.AtT_expression = None
        index_expressions = self.index_expressions
        self.index_expressions = []  # 退出时清空，避免重复记录
        self.list_index_expressions.append(ListIndexExpression(principal_expression, is_positive, index_expressions))

    # 获取单个的IndexExpression
    def exitS_SingleIndexExpression(self, ctx: s_cypherParser.S_SingleIndexExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = self.left_expression
        self.left_expression = None  # 退出置空
        index_expression = IndexExpression(left_expression, None)
        self.index_expressions.append(index_expression)

    # 获取成对的IndexExpression
    def exitS_DoubleIndexExpression(self, ctx: s_cypherParser.S_DoubleIndexExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = self.left_expression
        self.left_expression = None  # 退出置空
        right_expression = self.right_expression
        self.right_expression = None  # 退出置空
        index_expression = IndexExpression(left_expression, right_expression)
        self.index_expressions.append(index_expression)

    def exitS_LeftExpression(self, ctx: s_cypherParser.S_LeftExpressionContext):
        self.left_expression = self.expression

    def exitS_RightExpression(self, ctx: s_cypherParser.S_RightExpressionContext):
        self.right_expression = self.expression

    def exitOC_PropertyOrLabelsExpression(self, ctx: s_cypherParser.OC_PropertyOrLabelsExpressionContext):
        # atom: Atom,
        # property_chains: List[str] = None,
        # labels: List[str] = None
        atom = Atom(ctx.oC_Atom().getText())
        property_chains_list = self.property_look_up_list
        self.property_look_up_list = []  # 退出清空
        labels_list = self.node_labels
        self.node_labels = []  # 退出清空
        self.properties_labels_expression = PropertiesLabelsExpression(atom, property_chains_list, labels_list)

    def exitS_AtTExpression(self, ctx: s_cypherParser.S_AtTExpressionContext):
        # atom: Atom,
        # property_chains: List[str] = None,
        # is_value: bool = False,
        # time_property_chains: List[str] = None
        atom = Atom(ctx.oC_Atom().getText())
        is_value = False
        if ctx.PoundValue() is not None:
            is_value = True
        # 获取属性
        property_chains = self.property_look_up_list
        self.property_look_up_list = []  # 退出清空
        # 获取时间属性
        time_property_chains = self.property_look_up_time_list
        self.property_look_up_time_list = []  # 退出清空
        self.AtT_expression = AtTExpression(atom, property_chains, is_value, time_property_chains)

    def exitOC_PropertyLookup(self, ctx: s_cypherParser.OC_PropertyLookupContext):
        self.property_look_up_list.append(ctx.oC_PropertyKeyName().getText())

    def exitS_PropertyLookupTime(self, ctx: s_cypherParser.S_PropertyLookupTimeContext):
        self.property_look_up_time_list = self.property_look_up_list
        self.property_look_up_list = []  # 退出清空

    # =============处理WhereExpression===============
    def exitS_WhereExpression(self, ctx: s_cypherParser.S_WhereExpressionContext):
        self.where_expression = Expression(self.where_or_expression)

    def exitS_OrWhereExpression(self, ctx: s_cypherParser.S_OrWhereExpressionContext):
        self.where_or_expression = OrExpression(self.where_xor_expressions)
        self.where_xor_expressions = []  # 退出时清空，避免重复记录

    def exitS_XorWhereExpression(self, ctx: s_cypherParser.S_XorWhereExpressionContext):
        self.where_xor_expressions.append(XorExpression(self.where_and_expressions))
        self.where_and_expressions = []  # 退出时清空，避免重复记录

    def exitS_AndWhereExpression(self, ctx: s_cypherParser.S_AndWhereExpressionContext):
        self.where_and_expressions.append(AndExpression(self.where_not_expressions))
        self.where_not_expressions = []  # 退出时清空，避免重复记录

    def exitS_NotWhereExpression(self, ctx: s_cypherParser.S_NotWhereExpressionContext):
        is_not = False
        if ctx.NOT():
            is_not = True
        self.where_not_expressions.append(NotExpression(self.where_comparison_expression, is_not))

    def exitS_ComparisonWhereExpression(self, ctx: s_cypherParser.S_ComparisonWhereExpressionContext):
        # 获取比较运算符
        where_comparison_operations = self.operations
        self.operations = []  # 退出清空
        where_subject_expressions = self.where_subject_expressions
        self.where_subject_expressions = []  # 退出时清空，避免重复记录
        self.where_comparison_expression = ComparisonExpression(where_subject_expressions, where_comparison_operations)

    # 处理subject_expression
    def exitS_StringListNullPredicateWhereExpression(self,
                                                     ctx: s_cypherParser.S_StringListNullPredicateWhereExpressionContext):
        if len(self.where_add_subtract_expressions) > 0:
            where_add_or_subtract_expression = self.where_add_subtract_expressions[0]
            self.where_add_subtract_expressions = []  # 退出清空
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")
        where_predicate_expression = None
        if self.where_time_predicate_expression is not None:
            where_predicate_expression = self.where_time_predicate_expression
            self.where_time_predicate_expression = None
        elif self.where_string_predicate_expression is not None:
            where_predicate_expression = self.where_string_predicate_expression
            self.where_string_predicate_expression = None
        elif self.where_list_predicate_expression is not None:
            where_predicate_expression = self.where_list_predicate_expression
            self.where_list_predicate_expression = None
        elif self.where_null_predicate_expression is not None:
            where_predicate_expression = self.where_null_predicate_expression
            self.where_null_predicate_expression = None
        self.where_subject_expressions.append(
            SubjectExpression(where_add_or_subtract_expression, where_predicate_expression))

    def exitS_TimePredicateWhereExpression(self, ctx: s_cypherParser.S_TimePredicateWhereExpressionContext):
        time_str = ctx.getText()
        if 'DURING' in time_str and 'OVERLAPS' not in time_str:
            time_operation = 'DURING'
        elif 'DURING' not in time_str and 'OVERLAPS' in time_str:
            time_operation = 'OVERLAPS'
        else:
            raise FormatError("The time predicate expression must have the operation DURING or OVERLAPS.")
        if len(self.where_add_subtract_expressions) == 2:
            where_add_or_subtract_expression = self.where_add_subtract_expressions[1]
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")
        self.where_time_predicate_expression = TimePredicateExpression(time_operation, where_add_or_subtract_expression)

    def exitS_StringPredicateWhereExpression(self, ctx: s_cypherParser.S_StringPredicateWhereExpressionContext):
        string_str = ctx.getText()
        if 'STARTS' and 'WITH' in string_str:
            string_operation = 'STARTS WITH'
        elif 'ENDS' and 'WITH' in string_str:
            string_operation = 'ENDS WITH'
        elif 'CONTAINS' in string_str:
            string_operation = 'CONTAINS'
        else:
            raise FormatError("There must have an operation among 'STARTS WITH','ENDS WITH' and 'CONTAINS'.")
        if len(self.where_add_subtract_expressions) == 2:
            where_add_or_subtract_expression = self.where_add_subtract_expressions[1]
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")
        self.where_string_predicate_expression = StringPredicateExpression(string_operation,
                                                                           where_add_or_subtract_expression)

    def exitS_ListPredicateWhereExpression(self, ctx: s_cypherParser.S_ListPredicateWhereExpressionContext):
        if len(self.where_add_subtract_expressions) == 2:
            self.where_list_predicate_expression = ListPredicateExpression(self.where_add_subtract_expressions[1])
        else:
            raise FormatError("The number of AddOrSubtractExpression is wrong.")

    def exitS_NullPredicateWhereExpression(self, ctx: s_cypherParser.S_NullPredicateWhereExpressionContext):
        is_null = True
        if ctx.IS() and ctx.NOT() and ctx.NULL() is not None:
            is_null = False
        self.where_null_predicate_expression = NullPredicateExpression(is_null)

    def exitS_AddOrSubtractWhereExpression(self, ctx: s_cypherParser.S_AddOrSubtractWhereExpressionContext):
        # 获取加减运算符
        where_new_operations_list = self.operations
        self.operations = []  # 退出时清空
        # 暂时解决Atom运算符不匹配问题
        if '(' or ')' in ctx.getText():
            where_new_operations_list = []
        where_add_subtract_operations = None
        if len(where_new_operations_list) > 0:
            where_add_subtract_operations = where_new_operations_list
        where_multiply_divide_expressions = self.where_multiply_divide_expressions
        self.where_multiply_divide_expressions = []  # 退出时清空，避免重复记录
        self.where_add_subtract_expressions.append(AddSubtractExpression(where_multiply_divide_expressions,
                                                                         where_add_subtract_operations))

    def exitS_MultiplyDivideModuloWhereExpression(self,
                                                  ctx: s_cypherParser.S_MultiplyDivideModuloWhereExpressionContext):
        # 获取乘除模运算符
        where_new_operations_list = self.operations
        self.operations = []  # 退出时清空
        if '(' or ')' in ctx.getText():
            where_new_operations_list = []
        where_multiply_divide_operations = None
        if len(where_new_operations_list) > 0:
            where_multiply_divide_operations = where_new_operations_list
        where_power_expressions = self.where_power_expressions
        self.where_power_expressions = []  # 退出时清空，避免重复记录
        self.where_multiply_divide_expressions.append(
            MultiplyDivideExpression(where_power_expressions, where_multiply_divide_operations))

    def exitS_PowerOfWhereExpression(self, ctx: s_cypherParser.S_PowerOfWhereExpressionContext):
        where_new_power_expression = PowerExpression(self.where_list_index_expressions)
        self.where_power_expressions.append(where_new_power_expression)
        self.where_list_index_expressions = []  # 退出时清空，避免重复记录

    def exitS_UnaryAddOrSubtractWhereExpression(self, ctx: s_cypherParser.S_UnaryAddOrSubtractWhereExpressionContext):
        is_positive = True
        if '-' in ctx.getText():
            is_positive = False
        where_principal_expression = None
        if self.where_properties_labels_expression is not None:
            where_principal_expression = self.where_properties_labels_expression
            self.where_properties_labels_expression = None
        elif self.where_AtT_expression is not None:
            where_principal_expression = self.where_AtT_expression
            self.where_AtT_expression = None
        where_index_expressions = self.where_index_expressions
        self.where_index_expressions = []  # 退出时清空，避免重复记录
        self.where_list_index_expressions.append(
            ListIndexExpression(where_principal_expression, is_positive, where_index_expressions))

    # 获取单个的IndexExpression
    def exitS_SingleIndexWhereExpression(self, ctx: s_cypherParser.S_SingleIndexWhereExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = self.left_expression
        self.left_expression = None  # 退出置空
        index_expression = IndexExpression(left_expression, None)
        self.where_index_expressions.append(index_expression)

    # 获取成对的IndexExpression
    def exitS_DoubleIndexWhereExpression(self, ctx: s_cypherParser.S_DoubleIndexWhereExpressionContext):
        left_expression = self.left_expression
        self.left_expression = None  # 退出置空
        right_expression = self.right_expression
        self.right_expression = None  # 退出置空
        index_expression = IndexExpression(left_expression, right_expression)
        self.where_index_expressions.append(index_expression)

    def exitS_LeftWhereExpression(self, ctx: s_cypherParser.S_LeftWhereExpressionContext):
        self.left_expression = self.expression

    def exitS_RightWhereExpression(self, ctx: s_cypherParser.S_RightWhereExpressionContext):
        self.right_expression = self.expression

    def exitS_PropertyOrLabelsWhereExpression(self, ctx: s_cypherParser.S_PropertyOrLabelsWhereExpressionContext):
        atom = Atom(ctx.oC_Atom().getText())
        property_chains_list = self.property_look_up_list
        self.property_look_up_list = []  # 退出清空
        labels_list = self.node_labels
        self.node_labels = []  # 退出清空
        self.where_properties_labels_expression = PropertiesLabelsExpression(atom, property_chains_list, labels_list)

    def exitS_AtTWhereExpression(self, ctx: s_cypherParser.S_AtTWhereExpressionContext):
        atom = Atom(ctx.oC_Atom().getText())
        is_value = False
        if ctx.PoundValue() is not None:
            is_value = True
        # 获取属性
        property_chains = self.property_look_up_list
        self.property_look_up_list = []  # 退出清空
        # 获取时间属性
        time_property_chains = self.property_look_up_time_list
        self.property_look_up_time_list = []  # 退出清空
        self.where_AtT_expression = AtTExpression(atom, property_chains, is_value, time_property_chains)

    # 更新语句
    def exitOC_Create(self, ctx: s_cypherParser.OC_CreateContext):
        # patterns: List[Pattern]
        self.create_clause = CreateClause(self.patterns)
        self.patterns = []  # 退出时清空，避免重复记录

    def exitOC_Merge(self, ctx: s_cypherParser.OC_MergeContext):
        # patterns: List[Pattern],
        # actions: dict[str, SetClause] = None
        patterns = self.patterns
        actions = self.merge_actions
        self.merge_clause = MergeClause(patterns, actions)
        self.patterns = []  # 退出时清空
        self.merge_actions = dict()

    def exitOC_MergeAction(self, ctx: s_cypherParser.OC_MergeActionContext):
        merge_flag = 'CREATE'
        if 'MATCH' in ctx.getText():
            merge_flag = 'MATCH'
        self.merge_actions[merge_flag] = self.set_clause

    def exitOC_Delete(self, ctx: s_cypherParser.OC_DeleteContext):
        # delete_items: List[DeleteItem]
        self.delete_clause = DeleteClause(self.delete_items)
        self.delete_items = []  # 退出时清空，避免重复记录

    def exitS_DeleteItem(self, ctx: s_cypherParser.S_DeleteItemContext):
        # expression: Expression,
        # property_name: str = None,
        # is_value=False
        expression = self.expression
        property_name = None
        if ctx.oC_PropertyKeyName() is not None:
            property_name = ctx.oC_PropertyKeyName().getText()
        is_value = False
        if ctx.PoundValue() is not None:
            is_value = True
        self.delete_items.append(DeleteItem(expression, property_name, is_value))

    def exitOC_Set(self, ctx: s_cypherParser.OC_SetContext):
        # set_items: List[SetItem]
        self.set_clause = SetClause(self.set_items)
        self.set_items = []  # 退出清空

    def exitOC_SetItem(self, ctx: s_cypherParser.OC_SetItemContext):
        # 设置运算符
        set_item_str = ctx.getText()
        if '=' in set_item_str:
            operator = '='
        elif '+=' in set_item_str:
            operator = '+='
        elif '@T' in set_item_str:
            operator = '@T'
        elif ':' in set_item_str:
            operator = ':'
        else:
            operator = ''
        # object为对象节点变量名或者Atom表达式
        if ctx.oC_Variable() is not None:
            object_ = ctx.oC_Variable()
        else:
            object_ = ctx.oC_PropertyExpression().oC_Atom.getText()
        # 设置对象节点的label
        labels = None
        if ctx.oC_NodeLabels() is not None:
            labels = self.node_labels
            self.node_labels = []  # 退出清空
        # 设置值节点的值，或者表达式赋值
        value_expression = None
        if ctx.oC_Expression() is not None:
            value_expression = self.expression
        # 设置对象节点的有效时间
        object_interval = None
        if ctx.s_AtTElement() is not None:
            object_interval = self.getAtTElement(ctx.s_AtTElement().getText())
        # 设置属性节点的有效时间
        property_interval = None
        if ctx.s_SetPropertyItemOne() is not None:
            if ctx.s_SetPropertyItemOne().s_AtTElement() is not None:
                property_interval = self.getAtTElement(ctx.s_SetPropertyItemOne().s_AtTElement().getText())
        elif ctx.s_SetPropertyItemTwo() is not None:
            if ctx.s_SetPropertyItemTwo().s_AtTElement() is not None:
                property_interval = self.getAtTElement(ctx.s_SetPropertyItemTwo().s_AtTElement().getText())
        # 设置值节点的有效时间
        value_interval = None
        if ctx.s_SetValueItem() is not None:
            if ctx.s_SetValueItem().s_AtTElement() is not None:
                value_interval = self.getAtTElement(ctx.s_SetValueItem().s_AtTElement().getText())
        elif ctx.s_SetValueItemExpression() is not None:
            if ctx.s_SetValueItemExpression().s_AtTElement() is not None:
                value_interval = self.getAtTElement(ctx.s_SetValueItemExpression().s_AtTElement().getText())
        # 为属性节点名称，或者( SP? oC_PropertyLookup )+的字符串表示
        property_variable = None
        if ctx.s_SetPropertyItemTwo() is not None:
            if ctx.s_SetPropertyItemTwo().oC_PropertyKeyName() is not None:
                property_variable = ctx.s_SetPropertyItemTwo().oC_PropertyKeyName().getText()
        elif ctx.oC_PropertyExpression() is not None:
            if ctx.oC_PropertyExpression().oC_PropertyLookup() is not None:
                property_variable = ' '.join(self.property_look_up_list)
                self.property_look_up_list = []  # 退出清空
        self.set_items.append(
            SetItem(operator, object_, labels, object_interval, property_variable, property_interval, value_interval,
                    value_expression))

    def exitOC_Remove(self, ctx: s_cypherParser.OC_RemoveContext):
        # object_variable: str | Atom,
        # property_variable: str = None,
        # labels: List[str] = None
        object_variable = None
        if ctx.oC_RemoveItem().oC_Variable() is not None:
            object_variable = ctx.oC_RemoveItem().oC_Variable().getText()
        elif ctx.oC_RemoveItem().oC_PropertyExpression() is not None:
            object_variable = ctx.oC_RemoveItem().oC_PropertyExpression().oC_Atom.getText()
        # 为(SP? oC_PropertyLookup) + 的字符串表示
        property_variable = None
        if ctx.oC_RemoveItem().oC_PropertyExpression().oC_PropertyLookup() is not None:
            property_variable = ' '.join(self.property_look_up_list)
            self.property_look_up_list = []  # 退出清空
        labels = None
        if ctx.oC_RemoveItem().oC_NodeLabels() is not None:
            labels = self.node_labels
            self.node_labels = []  # 退出清空
        self.remove_clause = RemoveClause(object_variable, property_variable, labels)

    def exitS_Stale(self, ctx: s_cypherParser.S_StaleContext):
        # stale_items: List[DeleteItem]
        stale_items = self.stale_items
        self.stale_clause = StaleClause(stale_items)
        self.stale_items = []  # 退出清空

    def exitS_StaleItem(self, ctx: s_cypherParser.S_StaleItemContext):
        expression = self.expression
        property_name = None
        if ctx.oC_PropertyKeyName() is not None:
            property_name = ctx.oC_PropertyKeyName().getText()
        is_value = False
        if ctx.PoundValue() is not None:
            is_value = True
        self.stale_items.append(DeleteItem(expression, property_name, is_value))

    # 时间窗口限定
    def exitS_TimeWindowLimit(self, ctx: s_cypherParser.S_TimeWindowLimitContext):
        # time_window_limit: SnapshotClause | ScopeClause
        if ctx.s_Snapshot() is not None:
            self.time_window_limit_clause = TimeWindowLimitClause(self.snapshot_clause)
        elif ctx.s_Scope() is not None:
            self.time_window_limit_clause = TimeWindowLimitClause(self.scope_clause)

    def exitS_Snapshot(self, ctx: s_cypherParser.S_SnapshotContext):
        # time_point: Expression
        self.snapshot_clause = SnapshotClause(self.expression)

    def exitS_Scope(self, ctx: s_cypherParser.S_ScopeContext):
        # interval: Expression
        self.scope_clause = ScopeClause(self.expression)

    def exitOC_Atom(self, ctx: s_cypherParser.OC_AtomContext):
        pass
