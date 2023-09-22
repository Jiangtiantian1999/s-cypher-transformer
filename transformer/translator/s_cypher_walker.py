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

        # time
        self.at_time_clause = None
        # self.interval = None
        self.at_t_element = None

        # pattern
        self.patterns = []
        self.object_node_list = []
        self.edge_list = None

        # clauses
        self.multi_query_clauses = []
        self.single_query_clause = None
        self.union_query_clause = None
        self.with_clause = None

        self.reading_clauses = []
        self.match_clause = None
        self.unwind_clause = None
        self.call_clause = None
        self.return_clause = None
        self.between_clause = None
        self.order_by_clause = None
        self.yield_clause = None

        self.updating_clauses = []
        # UpdatingClause
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
        self.unary_add_subtract_expressions = []
        self.list_operation_expressions = []
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

    def exitOC_Union(self, ctx: s_cypherParser.OC_UnionContext):
        # multi_query_clauses: List[MultiQueryClause],
        # is_all: List[bool]
        if ctx.UNION() is not None:
            if "UNION ALL" in ctx.UNION().getText():
                self.union_is_all_list.append(True)
            else:
                self.union_is_all_list.append(False)
        print(len(self.multi_query_clauses), len(self.union_is_all_list))
        self.union_query_clause = UnionQueryClause(self.multi_query_clauses, self.union_is_all_list)
        # 待完善

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
        self.multi_query_clauses.append(MultiQueryClause(self.single_query_clause, self.with_query_clauses))

    def exitOC_SingleQuery(self, ctx: s_cypherParser.OC_SingleQueryContext):
        # reading_clauses: List[ReadingClause] = None,
        # updating_clauses: List[UpdatingClause] = None,
        # return_clause: ReadingClause
        self.single_query_clause = SingleQueryClause(self.reading_clauses, self.updating_clauses, self.return_clause)

    def exitOC_With(self, ctx: s_cypherParser.OC_WithContext):
        # projection_items: List[ProjectionItem],
        # is_distinct: bool = False,
        # order_by_clause: OrderByClause = None,
        # skip_expression: Expression = None,
        # limit_expression: Expression = None
        projection_items = self.projection_items
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
        elif self.call_clause is not None:
            reading_clause = ReadingClause(self.call_clause)
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
        if ctx.s_AtTime() is not None:
            time_window = self.at_time_clause
        elif ctx.s_Between() is not None:
            time_window = self.between_clause
        if ctx.oC_Where() is not None:
            where_expression = self.where_expression
        self.match_clause = MatchClause(patterns, is_optional, where_expression, time_window)

    def exitOC_Where(self, ctx: s_cypherParser.OC_WhereContext):
        expression = ctx.oC_Expression().getText()
        self.where_expression = Expression(expression)  # 先当作字符串来处理

    def exitS_Between(self, ctx: s_cypherParser.S_BetweenContext):
        # interval: Expression
        interval = ctx.oC_Expression().getText()
        self.between_clause = BetweenClause(Expression(interval))

    def exitS_AtTime(self, ctx: s_cypherParser.S_AtTimeContext):
        self.at_time_clause = AtTimeClause(Expression(ctx.oC_Expression().getText()))

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
        self.call_clause = CallClause(self.procedure_name, self.explicit_input_items, self.yield_clause)

    def exitOC_ProcedureName(self, ctx: s_cypherParser.OC_ProcedureNameContext):
        self.procedure_name = ctx.getText()

    def exitOC_YieldItems(self, ctx:s_cypherParser.OC_YieldItemsContext):
        # yield_items: dict[str, str],
        # where_expression: Expression = None
        self.yield_clause = YieldClause(self.yield_items, self.where_expression)

    def exitOC_YieldItem(self, ctx:s_cypherParser.OC_YieldItemContext):
        if ctx.oC_ProcedureResultField() is not None:
            self.yield_items[ctx.oC_ProcedureResultField().getText()] = ctx.oC_Variable().getText()
        else:
            self.yield_items[None] = ctx.oC_Variable().getText()

    # CALL查询
    def exitOC_StandaloneCall(self, ctx: s_cypherParser.OC_StandaloneCallContext):
        pass

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
            # interval = Interval(LocalDateTime(interval_from.strip('"')), TimePoint.NOW)
        else:
            at_t_element = AtTElement(TimePointLiteral(interval_from.strip('"')), TimePointLiteral(interval_to.strip('"')))
            # interval = Interval(LocalDateTime(interval_from.strip('"')), LocalDateTime(interval_to.strip('"')))
        return at_t_element

    # 获取对象节点
    def exitOC_NodePattern(self, ctx: s_cypherParser.OC_NodePatternContext):
        # node_content = ""  # 对象节点内容
        node_label_list = []  # 对象节点标签
        interval = None  # 对象节点时间
        properties = dict()  # 对象节点属性
        # if ctx.oC_Variable() is not None:
        #     node_content = ctx.oC_Variable().getText()
        if ctx.oC_NodeLabels() is not None:
            node_labels = ctx.oC_NodeLabels()
            if isinstance(node_labels, list):
                for node_label in node_labels:
                    node_label_list.append(node_label.getText().strip(':'))
            else:
                node_label_list.append(node_labels.getText().strip(':'))
        if ctx.s_AtTElement() is not None:
            n_interval = ctx.s_AtTElement()
            interval_str = n_interval.getText()
            interval = self.getAtTElement(interval_str)
        if ctx.s_Properties() is not None:
            properties = self.properties
        self.object_node_list.append(ObjectNode(node_label_list, None, interval, properties))

    def exitS_PropertiesPattern(self, ctx: s_cypherParser.S_PropertiesPatternContext):
        # 将属性节点和值节点组合成对象节点的属性
        for prop_node, val_node in zip(self.property_node_list, self.value_node_list):
            self.properties[prop_node] = val_node

    # 获取属性节点
    def exitS_PropertyNode(self, ctx: s_cypherParser.S_PropertyNodeContext):
        property_contents = []  # 属性节点内容
        property_intervals = []  # 属性节点时间
        # 获取属性节点内容
        if ctx.oC_PropertyKeyName() is not None:
            prop_contents = ctx.oC_PropertyKeyName()
            if isinstance(prop_contents, list):
                for prop_content in prop_contents:
                    property_contents.append(prop_content.getText())
            else:
                property_contents = [prop_contents.getText()]
        # 获取属性节点的时间
        if ctx.s_AtTElement() is not None:
            prop_intervals = ctx.s_AtTElement()
            if isinstance(prop_intervals, list):
                for prop_interval in prop_intervals:
                    interval_str = prop_interval.getText()
                    property_intervals.append(self.getAtTElement(interval_str))
            else:
                property_intervals = [self.getAtTElement(prop_intervals.getText())]
        # 构造属性节点列表
        for prop_content, prop_interval in zip(property_contents, property_intervals):
            self.property_node_list.append(PropertyNode(prop_content, None, prop_interval))

    # 获取值节点
    def exitS_ValueNode(self, ctx: s_cypherParser.S_ValueNodeContext):
        value_contents = []  # 值节点内容
        value_intervals = []  # 值节点时间
        # 获取值节点内容
        if ctx.oC_Expression() is not None:
            val_contents = ctx.oC_Expression()
            if isinstance(val_contents, list):
                for val_content in val_contents:
                    value_contents.append(val_content.getText())
            else:
                value_contents = [val_contents.getText()]
        # 获取值节点的时间
        if ctx.s_AtTElement() is not None:
            val_intervals = ctx.s_AtTElement()
            if isinstance(val_intervals, list):
                for val_interval in val_intervals:
                    interval_str = val_interval.getText()
                    value_intervals.append(self.getAtTElement(interval_str))
            else:
                value_intervals = [self.getAtTElement(val_intervals.getText())]
        # 构造值节点
        for val_content, val_interval in zip(value_contents, value_intervals):
            self.value_node_list.append(ValueNode(val_content, None, val_interval))

    # 获取时间
    def exitS_AtTElement(self, ctx: s_cypherParser.S_AtTElementContext):
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
            # self.interval = Interval(LocalDateTime(interval_from), TimePoint.NOW)
        else:
            self.at_t_element = AtTElement(TimePointLiteral(interval_from), TimePointLiteral(interval_to))
            # self.interval = Interval(LocalDateTime(interval_from), LocalDateTime(interval_to))

    def exitOC_RelationshipDetail(self, ctx: s_cypherParser.OC_RelationshipDetailContext):
        variable = ""
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        # interval = Interval(self.interval.interval_from, self.interval.interval_to)
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
        self.edge_list = SEdge('UNDIRECTED', variable, labels, length_tuple, interval, properties)

    def exitOC_RelationshipPattern(self, ctx: s_cypherParser.OC_RelationshipPatternContext):
        direction = 'UNDIRECTED'
        if ctx.oC_LeftArrowHead() is not None and ctx.oC_RightArrowHead() is None:
            direction = 'LEFT'
        elif ctx.oC_LeftArrowHead() is None and ctx.oC_RightArrowHead() is not None:
            direction = 'RIGHT'
        self.edge_list.direction = direction

    def exitOC_Pattern(self, ctx: s_cypherParser.OC_PatternContext):
        # nodes: List[ObjectNode],
        # edges: List[SEdge] = None,
        # variable: str = None
        nodes = self.object_node_list
        edges = self.edge_list
        self.patterns.append(Pattern(SPath(nodes, edges)))

    def exitOC_Return(self, ctx: s_cypherParser.OC_ReturnContext):
        # projection_items: List[ProjectionItem],
        # is_distinct: bool = False,
        # order_by_clause: OrderByClause = None,
        # skip_expression: Expression = None,
        # limit_expression: Expression = None
        projection_items = self.projection_items
        is_distinct = False
        if ctx.oC_ProjectionBody() and ctx.oC_ProjectionBody().DISTINCT() is not None:
            is_distinct = True
        order_by_clause = self.order_by_clause
        skip_expression = self.skip_expression
        limit_expression = self.limit_expression
        self.return_clause = ReturnClause(projection_items, is_distinct, order_by_clause, skip_expression, limit_expression)

    def exitOC_ProjectionItems(self, ctx: s_cypherParser.OC_ProjectionItemsContext):
        # is_all: bool = False,
        # expression: Exception = None,
        # variable: str = None
        is_all = False
        if '*' in ctx.getText():
            is_all = True
        projection_item = ctx.oC_ProjectionItem()
        variable = None
        if isinstance(projection_item, list):
            for item in projection_item:
                # expression的获取待处理
                expression = Expression(item.oC_Expression().getText())
                if item.oC_Variable is not None:
                    variable = item.oC_Variable()
                self.projection_items.append(ProjectionItem(is_all, expression, variable))
        else:
            expression = Expression(projection_item.oC_Expression().getText())
            variable = projection_item.oC_Variable().getText()
            self.projection_items.append(ProjectionItem(is_all, expression, variable))

    def exitOC_Order(self, ctx: s_cypherParser.OC_OrderContext):
        # sort_items: dict[Expression, str]
        self.order_by_clause = OrderByClause(self.sort_items)

    def exitOC_SortItem(self, ctx:s_cypherParser.OC_SortItemContext):
        expression = Expression(ctx.oC_Expression().getText())
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
        self.skip_expression = Expression(ctx.oC_Expression().getText())  # 暂以字符串的的形式存储

    def exitOC_Limit(self, ctx: s_cypherParser.OC_LimitContext):
        self.limit_expression = Expression(ctx.oC_Expression().getText())  # 暂以字符串的的形式存储

    def exitOC_Expression(self, ctx: s_cypherParser.OC_ExpressionContext):
        self.expression = Expression(self.or_expression)
        self.explicit_input_items.append(self.expression)

    def exitOC_OrExpression(self, ctx: s_cypherParser.OC_OrExpressionContext):
        # xor_expressions: List[XorExpression]
        self.or_expression = OrExpression(self.xor_expressions)

    def exitOC_XorExpression(self, ctx: s_cypherParser.OC_XorExpressionContext):
        # and_expressions: List[AndExpression]
        self.xor_expressions.append(XorExpression(self.and_expressions))

    def exitOC_AndExpression(self, ctx: s_cypherParser.OC_AndExpressionContext):
        # not_expressions: List[NotExpression]
        self.and_expressions.append(AndExpression(self.not_expressions))

    def exitOC_NotExpression(self, ctx: s_cypherParser.OC_NotExpressionContext):
        # comparison_expression: ComparisonExpression,
        # is_not=False
        is_not = False
        if ctx.NOT() is not None:
            is_not = True
        self.not_expressions.append(NotExpression(self.comparison_expression, is_not))

    # 运算符的获取
    @staticmethod
    def get_operations(expression: str, operations: list[str]) -> List[str]:
        # 设置字典，{运算符:[该运算符所在字符串的索引列表]}
        operation_index_dict = dict()
        for operation in operations:
            for index in re.finditer(operation, expression):
                operation_index_dict.setdefault(operation, []).append(index.start())  # 存入运算符的每一个首位索引
        # 按照索引大小对运算符进行排序存入新列表中
        total_num = len(expression)
        comparison_operations = [' '] * total_num
        for operation in operation_index_dict:
            index_list = operation_index_dict[operation]
            for index in index_list:
                comparison_operations[index - 1] = operation
        i = 0
        while i < len(comparison_operations):
            if comparison_operations[i] == ' ':
                comparison_operations.remove(comparison_operations[i])
            else:
                i += 1
        return comparison_operations

    def exitOC_ComparisonExpression(self, ctx: s_cypherParser.OC_ComparisonExpressionContext):
        # subject_expressions: List[SubjectExpression],
        # comparison_operations: List[str] = None
        # 第一个SubjectExpression不可少，后面每一个符号和一个SubjectExpression为一组合
        operations = ['=', '<>', '<', '>', '<=', '>=']
        # 获取比较运算符
        comparison_operations = self.get_operations(ctx.oC_PartialComparisonExpression().getText(), operations)
        subject_expressions = self.subject_expressions
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

    def exitOC_NullPredicateExpression(self, ctx: s_cypherParser.OC_NullPredicateExpressionContext):
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
        # 获取加减运算符
        operations = ['+', '-']
        add_subtract_operations = self.get_operations(ctx.getText(), operations)
        self.add_subtract_expression = AddSubtractExpression(multiply_divide_expressions, add_subtract_operations)

    def exitOC_MultiplyDivideModuloExpression(self, ctx: s_cypherParser.OC_MultiplyDivideModuloExpressionContext):
        # power_expressions: List[PowerExpression],
        # multiply_divide_operations: List[str] = None
        power_expressions = self.power_expressions
        # 获取乘除模运算符
        operations = ['*', '/', '%']
        multiply_divide_operations = self.get_operations(ctx.getText(), operations)
        self.multiply_divide_expressions.append(MultiplyDivideExpression(power_expressions, multiply_divide_operations))

    def exitOC_PowerOfExpression(self, ctx: s_cypherParser.OC_PowerOfExpressionContext):
        # list_index_expressions: List[ListIndexExpression]
        self.power_expressions.append(PowerExpression(self.list_index_expressions))

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
        self.list_index_expressions.append(ListIndexExpression(principal_expression, is_positive, index_expressions))

    # 获取单个的IndexExpression
    def exitOC_SingleIndexExpression(self, ctx: s_cypherParser.OC_SingleIndexExpressionContext):
        # left_expression,
        # right_expression=None
        left_expression = Expression(ctx.oC_Expression().getText())
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

    def exitOC_PropertyOrLabelsExpression(self, ctx: s_cypherParser.OC_PropertyOrLabelsExpressionContext):
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
        # 获取时间属性
        time_property_chains = self.property_look_up_time_list
        self.AtT_expression = AtTExpression(atom, property_chains, is_value, time_property_chains)

    def exitOC_PropertyLookup(self, ctx: s_cypherParser.OC_PropertyLookupContext):
        self.property_look_up_list.append(ctx.getText())

    def exitOC_PropertyLookupTime(self, ctx:s_cypherParser.OC_PropertyLookupTimeContext):
        self.property_look_up_time_list.append(ctx.oC_PropertyLookup().getText())

    # 更新语句
    def exitOC_Create(self, ctx: s_cypherParser.OC_CreateContext):
        pass

    def exitOC_Merge(self, ctx:s_cypherParser.OC_MergeContext):
        pass

    def exitOC_Delete(self, ctx:s_cypherParser.OC_DeleteContext):
        pass

    def exitOC_Set(self, ctx:s_cypherParser.OC_SetContext):
        pass

    def exitOC_Remove(self, ctx:s_cypherParser.OC_RemoveContext):
        pass

    def exitS_Stale(self, ctx:s_cypherParser.S_StaleContext):
        pass

    # 时间窗口限定
    def exitS_TimeWindowLimit(self, ctx:s_cypherParser.S_TimeWindowLimitContext):
        # time_window_limit: SnapshotClause | ScopeClause
        pass
