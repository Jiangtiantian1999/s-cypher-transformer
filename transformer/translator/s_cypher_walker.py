from transformer.grammar_parser.s_cypherListener import s_cypherListener
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_datetime import *
from transformer.ir.s_graph import *
from transformer.ir.s_expression import *
import re


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
        # self.interval = None
        self.at_t_element = None

        # pattern
        self.patterns = []
        self.object_node_list = []
        self.edge_list = []  # 存放所有边
        self.relationship_pattern = None  # 边模式SEdge
        self.pattern_element = None  # SPath
        self.path_function_pattern = None  # TemporalPathCall

        # clauses
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
        self.where_expression = None
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
        self.add_subtract_expression = None
        self.multiply_divide_expressions = []
        self.power_expressions = []
        self.list_index_expressions = []
        self.index_expressions = []
        self.AtT_expression = None
        self.properties_labels_expression = None

        # 中间变量
        self.with_query_clauses = []
        self.union_is_all_list = []
        self.projection_items = []
        self.property_look_up_list = []
        self.property_look_up_time_list = []
        self.sort_items = dict()
        self.yield_items = dict()
        self.procedure_name = None
        self.explicit_input_items = []  # 带参程序调用
        self.left_index_expression = None
        self.delete_items = []
        self.merge_actions = dict()
        self.set_items = []
        self.remove_items = []
        self.stale_items = []

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
        reading_clause = None
        if self.match_clause is not None:
            reading_clause = ReadingClause(self.match_clause)
        elif self.unwind_clause is not None:
            reading_clause = ReadingClause(self.unwind_clause)
        elif self.in_query_call_clause is not None:
            reading_clause = ReadingClause(self.in_query_call_clause)
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
        if ctx.oC_Where() is not None:
            where_expression = self.where_expression
        self.match_clause = MatchClause(patterns, is_optional, where_expression, time_window)

    def exitOC_Where(self, ctx: s_cypherParser.OC_WhereContext):
        self.where_expression = self.expression

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
        # yield_items: dict[str, str],
        # where_expression: Expression = None
        self.yield_clause = YieldClause(self.yield_items, self.where_expression)
        self.yield_items = dict()  # 退出清空

    def enterOC_YieldItem(self, ctx: s_cypherParser.OC_YieldItemContext):
        if ctx.oC_ProcedureResultField() is not None:
            self.yield_items[ctx.oC_ProcedureResultField().getText()] = ctx.oC_Variable().getText()
        else:
            self.yield_items[None] = ctx.oC_Variable().getText()

    # CALL查询
    def exitOC_StandaloneCall(self, ctx: s_cypherParser.OC_StandaloneCallContext):
        # procedure_name: str,
        # input_items: List[Expression] = None,
        # yield_clause: YieldClause = None
        input_items = None
        if ctx.oC_ExplicitProcedureInvocation() is not None:
            input_items = self.explicit_input_items
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
            at_t_element = AtTElement(TimePointLiteral(interval_from.strip('"')), TimePointLiteral(TimePoint.NOW))
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
    def enterS_PropertyNode(self, ctx: s_cypherParser.S_PropertyNodeContext):
        # 获取属性节点内容
        property_content = ctx.oC_PropertyKeyName().getText()  # 属性节点内容
        # 获取属性节点的时间
        property_interval = self.at_t_element  # 属性节点时间
        self.property_node_list.append(PropertyNode(property_content, None, property_interval))

    # 获取值节点
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
    def enterS_AtTElement(self, ctx: s_cypherParser.S_AtTElementContext):
        time_list = ctx.s_TimePointLiteral()
        now = ctx.NOW()
        if len(time_list) == 2 and now is None:
            interval_from = time_list[0].getText().strip('"')
            interval_to = time_list[1].getText().strip('"')
        elif len(time_list) == 1 and now is not None:
            interval_from = time_list[0].getText().strip('"')
            interval_to = ctx.NOW().getText().strip('"')
        else:
            raise FormatError("Invalid time format!")
        if interval_to == "NOW":
            self.at_t_element = AtTElement(TimePointLiteral(interval_from), TimePointLiteral(TimePoint.NOW))
        else:
            self.at_t_element = AtTElement(TimePointLiteral(interval_from), TimePointLiteral(interval_to))

    def exitOC_RelationshipDetail(self, ctx: s_cypherParser.OC_RelationshipDetailContext):
        variable = ""
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        interval = self.at_t_element
        lengths = ctx.oC_RangeLiteral().oC_IntegerLiteral()
        length_tuple = tuple()
        for length in lengths:
            length_tuple.__add__(length)
        labels = ctx.oC_RelationshipTypes()
        labels_list = []
        for label in labels:
            labels_list.append(label.getText())
        properties = ctx.oC_Properties()
        property_list = []
        for property_ in property_list:
            property_list.append(property_.getText())
        self.relationship_pattern = SEdge('UNDIRECTED', variable, labels, length_tuple, interval, properties)

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

    def exitOC_Pattern(self, ctx: s_cypherParser.OC_PatternContext):
        # pattern: SPath | TemporalPathCall
        pattern = None
        if self.path_function_pattern is not None:
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
        # projection_item = ctx.oC_ProjectionItem()
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
        if len(ctx.NOT()) > 1:
            is_not = True
        self.not_expressions.append(NotExpression(self.comparison_expression, is_not))

    # 运算符的获取
    @staticmethod
    def get_operations(expression: str, operations: list[str]) -> List[str]:
        # 设置字典，{运算符:[该运算符所在字符串的索引列表]}
        operation_index_dict = dict()
        for operation in operations:
            pattern = re.compile("{}".format('[' + operation + ']'))
            it = re.finditer(pattern, expression)  # 在输入的expression字符串中找到匹配operation的所有子串，返回迭代器
            # for index in re.finditer(operation, expression):
            if it is not None:
                for index in it:
                    operation_index_dict.setdefault(operation, []).append(index.start())  # 存入运算符的每一个首位索引
                    # operation_index_dict.setdefault(operation, []).append(match.group())
        # 按照索引大小对运算符进行排序存入新列表中
        total_num = len(expression)
        new_operations = [' '] * total_num
        for operation in operation_index_dict:
            index_list = operation_index_dict[operation]
            for index in index_list:
                new_operations[index - 1] = operation
        i = 0
        while i < len(new_operations):
            if new_operations[i] == ' ':
                new_operations.remove(new_operations[i])
            else:
                i += 1
        return new_operations

    def exitOC_ComparisonExpression(self, ctx: s_cypherParser.OC_ComparisonExpressionContext):
        # subject_expressions: List[SubjectExpression],
        # comparison_operations: List[str] = None
        # 第一个SubjectExpression不可少，后面每一个符号和一个SubjectExpression为一组合
        operations = ['=', '<>', '<', '>', '<=', '>=']
        # 获取比较运算符
        comparison_operations = []
        if isinstance(ctx.oC_PartialComparisonExpression(), list):
            for partial_comparison in ctx.oC_PartialComparisonExpression():
                comparison_operations.extend(self.get_operations(partial_comparison.getText(), operations))
        else:
            comparison_operations.extend(
                self.get_operations(ctx.oC_PartialComparisonExpression().getText(), operations))
        subject_expressions = self.subject_expressions
        self.subject_expressions = []  # 退出时清空，避免重复记录
        self.comparison_expression = ComparisonExpression(subject_expressions, comparison_operations)

    # 处理subject_expression
    def exitOC_StringListNullPredicateExpression(self, ctx: s_cypherParser.OC_StringListNullPredicateExpressionContext):
        # add_or_subtract_expression: AddSubtractExpression,
        # predicate_expression: TimePredicateExpression | StringPredicateExpression | ListPredicateExpression | NullPredicateExpression = None
        add_or_subtract_expression = self.add_subtract_expression
        predicate_expression = None
        if self.time_predicate_expression is not None:
            predicate_expression = self.time_predicate_expression
        elif self.string_predicate_expression is not None:
            predicate_expression = self.string_predicate_expression
        elif self.list_predicate_expression is not None:
            predicate_expression = self.list_predicate_expression
        elif self.null_predicate_expression is not None:
            predicate_expression = self.null_predicate_expression
        self.subject_expressions.append(SubjectExpression(add_or_subtract_expression, predicate_expression))

    def enterOC_NullPredicateExpression(self, ctx: s_cypherParser.OC_NullPredicateExpressionContext):
        is_null = True
        if ctx.IS() and ctx.NOT() and ctx.NULL() is not None:
            is_null = False
        self.null_predicate_expression = NullPredicateExpression(is_null)

    def exitOC_ListPredicateExpression(self, ctx: s_cypherParser.OC_ListPredicateExpressionContext):
        # add_or_subtract_expression: AddSubtractExpression = None
        self.list_predicate_expression = ListPredicateExpression(self.add_subtract_expression)

    def exitS_TimePredicateExpression(self, ctx: s_cypherParser.S_TimePredicateExpressionContext):
        # time_operation: str,
        # add_or_subtract_expression: AddSubtractExpression = None
        time_operation = ''
        if ctx.DURING() is not None and ctx.OVERLAPS() is None:
            time_operation = 'DURING'
        elif ctx.DURING() is None and ctx.OVERLAPS() is not None:
            time_operation = 'OVERLAPS'
        else:
            raise FormatError("The time predicate expression must have the operation DURING or OVERLAPS.")
        add_or_subtract_expression = self.add_subtract_expression
        self.time_predicate_expression = TimePredicateExpression(time_operation, add_or_subtract_expression)

    def exitOC_StringPredicateExpression(self, ctx: s_cypherParser.OC_StringPredicateExpressionContext):
        # string_operation: str,
        # add_or_subtract_expression: AddSubtractExpression = None
        string_operation = ''
        if ctx.STARTS() and ctx.WITH() is not None:
            string_operation = 'STARTS WITH'
        elif ctx.ENDS() and ctx.WITH() is not None:
            string_operation = 'ENDS WITH'
        elif ctx.CONTAINS() is not None:
            string_operation = 'CONTAINS'
        else:
            raise FormatError("There must have an operation among 'STARTS WITH','ENDS WITH' and 'CONTAINS'.")
        add_or_subtract_expression = self.add_subtract_expression
        self.string_predicate_expression = StringPredicateExpression(string_operation, add_or_subtract_expression)

    def exitOC_AddOrSubtractExpression(self, ctx: s_cypherParser.OC_AddOrSubtractExpressionContext):
        # multiply_divide_expressions: List[MultiplyDivideExpression],
        # add_subtract_operations: List[str] = None
        multiply_divide_expressions = self.multiply_divide_expressions
        self.multiply_divide_expressions = []  # 退出时清空，避免重复记录
        # 获取加减运算符
        operations = ['+', '-']
        add_subtract_operations = self.get_operations(ctx.getText(), operations)
        self.add_subtract_expression = AddSubtractExpression(multiply_divide_expressions, add_subtract_operations)

    def exitOC_MultiplyDivideModuloExpression(self, ctx: s_cypherParser.OC_MultiplyDivideModuloExpressionContext):
        # power_expressions: List[PowerExpression],
        # multiply_divide_operations: List[str] = None
        power_expressions = self.power_expressions
        self.power_expressions = []  # 退出时清空，避免重复记录
        # 获取乘除模运算符
        operations = ['*', '/', '%']
        new_operations_list = self.get_operations(ctx.getText(), operations)
        multiply_divide_operations = None
        if len(new_operations_list) > 0:
            multiply_divide_operations = new_operations_list
        self.multiply_divide_expressions.append(MultiplyDivideExpression(power_expressions, multiply_divide_operations))

    def exitOC_PowerOfExpression(self, ctx: s_cypherParser.OC_PowerOfExpressionContext):
        # list_index_expressions: List[ListIndexExpression]
        self.power_expressions.append(PowerExpression(self.list_index_expressions))
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
        elif self.AtT_expression is not None:
            principal_expression = self.AtT_expression
        index_expressions = self.index_expressions
        self.index_expressions = []  # 退出时清空，避免重复记录
        self.list_index_expressions.append(ListIndexExpression(principal_expression, is_positive, index_expressions))

    # 获取单个的IndexExpression
    def exitOC_SingleIndexExpression(self, ctx: s_cypherParser.OC_SingleIndexExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = Expression(ctx.oC_Expression().getText())
        # left_expression = self.expression
        index_expression = IndexExpression(left_expression, None)
        self.index_expressions.append(index_expression)

    # 获取成对的IndexExpression
    def exitOC_DoubleIndexExpression(self, ctx: s_cypherParser.OC_DoubleIndexExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = Expression(ctx.oC_Expression().getText())
        right_expression = Expression(ctx.oC_Expression().getText())
        index_expression = IndexExpression(left_expression, right_expression)
        self.index_expressions.append(index_expression)

    def enterOC_PropertyOrLabelsExpression(self, ctx: s_cypherParser.OC_PropertyOrLabelsExpressionContext):
        # atom: Atom,
        # property_chains: List[str] = None,
        # labels: List[str] = None
        atom = Atom(ctx.oC_Atom().getText())
        property_chains = ctx.oC_PropertyLookup()
        property_chains_list = []
        if isinstance(property_chains, list):
            for property_chain in property_chains:
                property_chains_list.append(property_chain.getText())
        else:
            property_chains_list.append(property_chains.getText())
        labels = ctx.oC_NodeLabels()
        labels_list = []
        if labels is not None:
            if isinstance(labels, list):
                for label in labels:
                    labels_list.append(label.getText())
            else:
                labels_list.append(labels.getText())
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

    def enterOC_PropertyLookup(self, ctx: s_cypherParser.OC_PropertyLookupContext):
        self.property_look_up_list.append(ctx.getText())

    def enterOC_PropertyLookupTime(self, ctx: s_cypherParser.OC_PropertyLookupTimeContext):
        self.property_look_up_time_list.append(ctx.oC_PropertyLookup().getText())

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

    def exitOC_SetItem(self, ctx:s_cypherParser.OC_SetItemContext):
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
        if ctx.s_SetPropertyItemOne().s_AtTElement() is not None:
            property_interval = self.getAtTElement(ctx.s_SetPropertyItemOne().s_AtTElement().getText())
        elif ctx.s_SetPropertyItemTwo().s_AtTElement() is not None:
            property_interval = self.getAtTElement(ctx.s_SetPropertyItemTwo().s_AtTElement().getText())
        # 设置值节点的有效时间
        value_interval = None
        if ctx.s_SetValueItem().s_AtTElement() is not None:
            value_interval = self.getAtTElement(ctx.s_SetValueItem().s_AtTElement().getText())
        elif ctx.s_SetValueItemExpression().s_AtTElement() is not None:
            value_interval = self.getAtTElement(ctx.s_SetValueItemExpression().s_AtTElement().getText())
        # 为属性节点名称，或者( SP? oC_PropertyLookup )+的字符串表示
        property_variable = None
        if ctx.s_SetPropertyItemTwo().oC_PropertyKeyName() is not None:
            property_variable = ctx.s_SetPropertyItemTwo().oC_PropertyKeyName().getText()
        elif ctx.oC_PropertyExpression().oC_PropertyLookup() is not None:
            property_variable = ' '.join(self.property_look_up_list)
            self.property_look_up_list = []  # 退出清空
        self.set_items.append(SetItem(operator, object_, labels, object_interval, property_variable, property_interval, value_interval, value_expression))

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

    def enterS_Snapshot(self, ctx: s_cypherParser.S_SnapshotContext):
        # time_point: Expression
        self.snapshot_clause = SnapshotClause(self.expression)

    def enterS_Scope(self, ctx: s_cypherParser.S_ScopeContext):
        # interval: Expression
        self.scope_clause = ScopeClause(self.expression)
