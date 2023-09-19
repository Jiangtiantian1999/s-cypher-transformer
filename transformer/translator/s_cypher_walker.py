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
        self.at_time = None
        self.interval = None
        # pattern
        self.patterns = []
        self.object_node_list = []
        self.edge_list = None
        # path
        self.path_function_name = ""
        # clauses
        self.multi_query_clauses = []
        self.match_clause = None
        self.with_clause = None

        self.where_clause = None
        self.reading_clause = None
        self.unwind_clause = None
        self.inner_call_clause = None
        self.order_by_clause = None
        self.skip_clause = None
        self.limit_clause = None

        self.return_clause = None
        self.projection_items = []

        self.updating_clause = None
        self.single_query_clause = None
        self.with_query_clause = None
        self.union_query_clause = None
        self.stand_alone_call_clause = None
        self.time_window_limit_clause = None

        # expression
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
        self.at_t_expression = None
        self.properties_labels_expression = None

    def exitOC_Union(self, ctx: s_cypherParser.OC_UnionContext):
        # multi_query_clauses: List[MultiQueryClause],
        # is_all: List[bool]
        # ---------test match--------
        is_all_list = []
        if "UNION ALL" in ctx.UNION().getText():
            is_all_list.append(True)
        else:
            is_all_list.append(False)
        self.union_query_clause = UnionQueryClause(self.multi_query_clauses, is_all_list)

    def exitOC_MultiPartQuery(self, ctx: s_cypherParser.OC_MultiPartQueryContext):
        # single_query_clause: SingleQueryClause = None,
        # with_query_clauses: List[WithQueryClause] = None
        pass

    def exitOC_SingleQuery(self, ctx: s_cypherParser.OC_SingleQueryContext):
        # reading_clauses: List[ReadingClause] = None,
        # updating_clauses: List[UpdatingClause] = None,
        # return_clause: ReadingClause
        # -----------------是不是要换成ReturnClause-------------
        pass

    def exitOC_With(self, ctx:s_cypherParser.OC_WithContext):
        #  with_clause: WithClause,
        #  reading_clauses: List[ReadingClause] = None,
        #  updating_clauses: List[UpdatingClause] = None
        pass

    def enterOC_ReadingClause(self, ctx: s_cypherParser.OC_ReadingClauseContext):
        match_clause = None
        unwind_clause = None
        in_query_call_clause = None
        if ctx.oC_Match() is not None:
            self.reading_clause = ReadingClause(self.match_clause)
        elif ctx.oC_Unwind() is not None:
            self.reading_clause = ReadingClause(self.unwind_clause)
        elif ctx.oC_InQueryCall() is not None:
            self.reading_clause = ReadingClause(self.inner_call_clause)
        else:
            pass

    def exitOC_ReadingClause(self, ctx:s_cypherParser.OC_ReadingClauseContext):
        # reading_clause: MatchClause | UnwindClause | CallClause
        pass

    def exitOC_Match(self, ctx: s_cypherParser.OC_MatchContext):
        is_optional = False
        patterns = []
        time_window = None
        where_clause = None
        if ctx.OPTIONAL() is not None:
            is_optional = True
        if ctx.oC_Pattern() is not None:
            patterns = self.patterns
        if ctx.s_AtTime() is not None:
            time_window = self.at_time
        elif ctx.s_Between() is not None:
            time_window = self.interval
        if ctx.oC_Where() is not None:
            where_clause = self.where_clause
        self.match_clause = MatchClause(patterns, is_optional, where_clause, time_window)

    def enterOC_Where(self, ctx: s_cypherParser.OC_WhereContext):
        expression = ctx.oC_Expression().getText()
        self.where_clause = WhereClause(expression)  # where子句待处理

    def enterS_Between(self, ctx: s_cypherParser.S_BetweenContext):
        # 时间区间左右节点的获取待添加
        self.interval = ctx.oC_Expression().getText()

    def enterS_AtTime(self, ctx: s_cypherParser.S_AtTimeContext):
        self.at_time = ctx.oC_Expression().getText()

    def enterOC_Unwind(self, ctx:s_cypherParser.OC_UnwindContext):
        self.unwind_clause = ctx.UNWIND().getText()

    def enterOC_InQueryCall(self, ctx:s_cypherParser.OC_InQueryCallContext):
        self.inner_call_clause = ctx.CALL().getText()

    @staticmethod
    def getInterval(interval_str) -> Interval:
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
            interval = Interval(LocalDateTime(interval_from.strip('"')), TimePoint.NOW)
        else:
            interval = Interval(LocalDateTime(interval_from.strip('"')), LocalDateTime(interval_to.strip('"')))
        return interval

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
            interval = self.getInterval(interval_str)
        if ctx.s_Properties() is not None:
            properties = self.properties
        self.object_node_list.append(ObjectNode(node_label_list, None, interval, properties))

    def exitS_PropertiesPattern(self, ctx: s_cypherParser.S_PropertiesPatternContext):
        # 将属性节点和值节点组合成对象节点的属性
        for prop_node, val_node in zip(self.property_node_list, self.value_node_list):
            self.properties[prop_node] = val_node

    # 获取属性节点
    def enterS_PropertyNode(self, ctx: s_cypherParser.S_PropertyNodeContext):
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
                    property_intervals.append(self.getInterval(interval_str))
            else:
                property_intervals = [self.getInterval(prop_intervals.getText())]
        # 构造属性节点列表
        for prop_content, prop_interval in zip(property_contents, property_intervals):
            self.property_node_list.append(PropertyNode(prop_content, None, prop_interval))

    # 获取值节点
    def enterS_ValueNode(self, ctx: s_cypherParser.S_ValueNodeContext):
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
                    value_intervals.append(self.getInterval(interval_str))
            else:
                value_intervals = [self.getInterval(val_intervals.getText())]
        # 构造值节点
        for val_content, val_interval in zip(value_contents, value_intervals):
            self.value_node_list.append(ValueNode(val_content, None, val_interval))

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
            self.interval = Interval(LocalDateTime(interval_from), TimePoint.NOW)
        else:
            self.interval = Interval(LocalDateTime(interval_from), LocalDateTime(interval_to))

    def enterOC_RelationshipDetail(self, ctx: s_cypherParser.OC_RelationshipDetailContext):
        variable = ""
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        interval = Interval(self.interval.interval_from, self.interval.interval_to)
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

    def exitOC_RelationshipPattern(self, ctx:s_cypherParser.OC_RelationshipPatternContext):
        direction = 'UNDIRECTED'
        if ctx.oC_LeftArrowHead() is not None and ctx.oC_RightArrowHead() is None:
            direction = 'LEFT'
        elif ctx.oC_LeftArrowHead() is None and ctx.oC_RightArrowHead() is not None:
            direction = 'RIGHT'
        self.edge_list.direction = direction

    # def exitOC_AnonymousPatternPart(self, ctx: s_cypherParser.OC_AnonymousPatternPartContext):
    #     if self.object_node_list is not None:
    #         self.match_patterns.append(self.object_node_list)
    #         if self.edge_list is not None:
    #             self.match_patterns.append(self.edge_list)
    #     else:
    #         self.match_patterns.append(ctx.oC_PatternElement().getText())

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
        # skip_clause: SkipClause = None,
        # limit_clause: LimitClause = None
        projection_items = self.projection_items
        is_distinct = False
        if ctx.oC_ProjectionBody() and ctx.oC_ProjectionBody().DISTINCT() is not None:
            is_distinct = True
        order_by_clause = self.order_by_clause
        skip_clause = self.skip_clause
        limit_clause = self.limit_clause
        self.return_clause = ReturnClause(projection_items, is_distinct, order_by_clause, skip_clause, limit_clause)

    def enterOC_ProjectionItems(self, ctx:s_cypherParser.OC_ProjectionItemsContext):
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
                expression = item.oC_Expression().getText()
                if item.oC_Variable is not None:
                    variable = item.oC_Variable()
                self.projection_items.append(ProjectionItem(is_all, expression, variable))
        else:
            expression = projection_item.oC_Expression().getText()
            variable = projection_item.oC_Variable().getText()
            self.projection_items.append(ProjectionItem(is_all, expression, variable))

    def exitOC_Expression(self, ctx: s_cypherParser.OC_ExpressionContext):
        self.expression = Expression(self.or_expression)

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
    def exitOC_StringListNullPredicateExpression(self, ctx:s_cypherParser.OC_StringListNullPredicateExpressionContext):
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

    def exitOC_AddOrSubtractExpression(self, ctx: s_cypherParser.OC_AddOrSubtractExpressionContext):
        # multiply_divide_expressions: List[MultiplyDivideExpression],
        # add_subtract_operations: List[str] = None
        multiply_divide_expressions = self.multiply_divide_expressions
        # 获取加减运算符
        operations = ['+', '-']
        add_subtract_operations = self.get_operations(ctx.getText(), operations)
        self.add_subtract_expression = AddSubtractExpression(multiply_divide_expressions, add_subtract_operations)
        
    def exitOC_MultiplyDivideModuloExpression(self, ctx:s_cypherParser.OC_MultiplyDivideModuloExpressionContext):
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

    def exitOC_UnaryAddOrSubtractExpression(self, ctx:s_cypherParser.OC_UnaryAddOrSubtractExpressionContext):
        # ListIndexExpression的参数如下
        # principal_expression: PropertiesLabelsExpression | AtTExpression,
        # is_positive=True,
        # index_expression=None
        is_positive = True
        if '-' in ctx.getText():
            is_positive = False
        principal_expression = None
        index_expression = None
        if self.properties_labels_expression is not None:
            principal_expression = self.properties_labels_expression
        elif self.at_t_expression is not None:
            principal_expression = self.at_t_expression
        # 待补充oC_Expression
        index_expression = ctx.oC_ListOperatorExpression().oC_Expression.getText()
        self.list_index_expressions.append(ListIndexExpression(principal_expression, is_positive, index_expression))

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
        if isinstance(labels, list):
            for label in labels:
                labels_list.append(label.getText())
        else:
            labels_list.append(labels.getText())
        self.properties_labels_expression = PropertiesLabelsExpression(atom, property_chains_list, labels_list)

    def exitS_AtTExpression(self, ctx:s_cypherParser.S_AtTExpressionContext):
        # atom: Atom,
        # property_chains: List[str] = None,
        # is_value: bool = False,
        # time_property_chains: List[str] = None
        atom = Atom(ctx.oC_Atom().getText())
        property_chains = ctx.oC_PropertyLookup()
        property_chains_list = []
        if isinstance(property_chains, list):
            for property_chain in property_chains:
                property_chains_list.append(property_chain.getText())
        else:
            property_chains_list.append(property_chains.getText())
        is_value = False
        if ctx.PoundValue() is not None:
            is_value = True
        time_property_chains = None  # 修改语法文件，区分Propertylookup
        self.at_t_expression = AtTExpression(atom, property_chains, is_value, time_property_chains)

    def exitS_TimePredicateExpression(self, ctx:s_cypherParser.S_TimePredicateExpressionContext):
        # time_operation: str,
        # add_or_subtract_expression: AddSubtractExpression = None
        time_operation = ''
        if ctx.DURING() is not None and ctx.OVERLAPS() is None:
            time_operation = 'DURING'
        elif ctx.DURING() is None and ctx.OVERLAPS() is not None:
            time_operation = 'OVEERLAPS'
        else:
            raise FormatError("The time predicate expression must have the operation DURING or OVERLAPS.")
        add_or_subtract_expression = self.add_subtract_expression
        self.time_predicate_expression = TimePredicateExpression(time_operation, add_or_subtract_expression)

    def exitOC_StringPredicateExpression(self, ctx:s_cypherParser.OC_StringPredicateExpressionContext):
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


