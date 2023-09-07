from transformer.grammar_parser.s_cypherListener import s_cypherListener
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_pattern import *


# This class records important information about the query
class SCypherWalker(s_cypherListener):
    def __init__(self, parser: s_cypherParser):
        self.parser = parser
        # node
        self.node_labels = []
        self.properties_pattern = []
        # time
        self.at_t_element = AtTElement(Time(), NOW())
        self.at_time = TimePoint()
        self.interval = None
        # pattern
        self.pattern_variable = ""
        self.match_patterns = []
        self.node_pattern = []
        self.relationship_pattern = SEdge('UNDIRECTED')
        # path
        self.path_function_name = ""
        # clauses
        self.match_clause = MatchClause()
        self.where_clause = None
        self.reading_clause = None
        self.unwind_clause = None
        self.inner_call_clause = None
        self.order_by_clause = None
        self.skip_clause = None
        self.limit_clause = None
        self.return_clause = None
        self.updating_clause = None
        self.single_query_clause = None
        self.with_clause = None
        self.with_query_clause = None
        self.multi_query_clause = []
        self.union_query_clause = None
        self.stand_alone_call_clause = None
        self.time_window_limit_clause = None

    def enterOC_Match(self, ctx: s_cypherParser.OC_MatchContext):
        if ctx.OPTIONAL() is not None:
            self.match_clause.is_optional = True
        if ctx.oC_Pattern() is not None:
            self.match_clause.patterns = self.match_patterns
        if ctx.s_AtTime() is not None:
            self.match_clause.time_window = self.at_time
        elif ctx.s_Between() is not None:
            self.match_clause.time_window = self.interval
        if ctx.oC_Where() is not None:
            self.match_clause.where_clause = self.where_clause

    def enterOC_Where(self, ctx: s_cypherParser.OC_WhereContext):
        expression = ctx.oC_Expression().getText()
        self.where_clause = WhereClause(expression)

    def enterS_Between(self, ctx:s_cypherParser.S_BetweenContext):
        # 时间区间左右节点的获取待添加
        self.interval = ctx.oC_Expression().getText()

    def enterS_AtTime(self, ctx: s_cypherParser.S_AtTimeContext):
        self.at_time = ctx.oC_Expression().getText()

    def enterOC_Unwind(self, ctx:s_cypherParser.OC_UnwindContext):
        pass

    def enterOC_InQueryCall(self, ctx:s_cypherParser.OC_InQueryCallContext):
        pass

    def enterOC_ReadingClause(self, ctx:s_cypherParser.OC_ReadingClauseContext):
        match_clause = None
        unwind_clause = None
        in_query_call_clause = None
        if ctx.oC_Match() is not None:
            match_clause = self.match_clause
        if ctx.oC_Unwind() is not None:
            unwind_clause = self.unwind_clause
        if ctx.oC_InQueryCall() is not None:
            in_query_call_clause = self.inner_call_clause
        self.reading_clause = ReadingClause(match_clause, unwind_clause, in_query_call_clause)

    def enterOC_PatternPart(self, ctx: s_cypherParser.OC_PatternPartContext):
        pattern = None
        if ctx.oC_Variable() is not None:
            self.pattern_variable = ctx.oC_Variable().getText()
            if ctx.s_PathFunctionPattern() is not None:
                pattern = ctx.s_PathFunctionPattern().getText()
            elif ctx.oC_AnonymousPatternPart() is not None:
                pattern = ctx.oC_AnonymousPatternPart().getText()
        else:
            pattern = ctx.oC_AnonymousPatternPart()

    def enterOC_NodePattern(self, ctx: s_cypherParser.OC_NodePatternContext):
        node_variable = ""
        node_label_list = []
        at_time_element = None
        property_list = []
        if ctx.oC_Variable() is not None:
            node_variable = ctx.oC_Variable().getText()
        if ctx.oC_NodeLabels() is not None:
            node_labels = ctx.oC_NodeLabels()
            for node_label in node_labels:
                node_label_list.append(node_label.getText())
        if ctx.s_AtTElement() is not None:
            at_time_element = self.at_t_element
        if ctx.s_Properties() is not None:
            property_list = self.properties_pattern
        self.node_pattern = NodePattern(node_variable, node_label_list, at_time_element, property_list)

    def enterS_AtTElement(self, ctx:s_cypherParser.S_AtTElementContext):
        time_list = ctx.s_TimePointLiteral()
        if len(time_list) == 2:
            self.at_t_element.time_from = Time(time_list[0].getText())
            self.at_t_element.time_to = Time(time_list[1].getText())
        elif len(time_list) == 1:
            self.at_t_element.time_from = Time(time_list[0].getText())
            self.at_t_element.time_to = NOW(ctx.NOW().getText())
        else:
            raise FormatError("Invalid time element format!")

    def enterS_PropertiesPattern(self, ctx:s_cypherParser.S_PropertiesPatternContext):
        property_key_names = []
        property_at_t_elements = []
        property_expressions = []
        if ctx.oC_PropertyKeyName() is not None:
            prop_key_names = ctx.oC_PropertyKeyName()
            for prop_key_name in prop_key_names:
                property_key_names.append(prop_key_name.getText())
        if ctx.s_AtTElement() is not None:
            prop_at_t_elements = ctx.s_AtTElement()
            for prop_at_t_element in prop_at_t_elements:
                property_at_t_elements.append(prop_at_t_element.getText())
        if ctx.oC_Expression() is not None:
            prop_expressions = ctx.oC_Expression()
            for prop_expression in prop_expressions:
                property_expressions.append(prop_expression.getText())
        # 添加时间与键值对应匹配的判断
        for key_name, at_t_element, expression in zip(property_key_names, property_at_t_elements, property_expressions):
            self.properties_pattern.append(PropertiesPattern(key_name, at_t_element, expression))

    def enterOC_RelationshipDetail(self, ctx: s_cypherParser.OC_RelationshipDetailContext):
        variable = ""
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        interval = Interval(self.at_t_element.time_from, self.at_t_element.time_to)
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
        self.relationship_pattern = SEdge(None, variable, labels, length_tuple, interval, properties)

    def enterOC_RelationshipPattern(self, ctx:s_cypherParser.OC_RelationshipPatternContext):
        direction = 'UNDIRECTED'
        if ctx.oC_LeftArrowHead() is not None and ctx.oC_RightArrowHead() is None:
            direction = 'LEFT'
        elif ctx.oC_LeftArrowHead() is None and ctx.oC_RightArrowHead() is not None:
            direction = 'RIGHT'
        self.relationship_pattern.direction = direction

    def enterOC_AnonymousPatternPart(self, ctx: s_cypherParser.OC_AnonymousPatternPartContext):
        pass

    def enterOC_Expression(self, ctx:s_cypherParser.OC_ExpressionContext):
        pass

    def enterOC_Return(self, ctx:s_cypherParser.OC_ReturnContext):
        projection_items = ctx.oC_ProjectionBody().oC_ProjectionItems().oC_ProjectionItem()
        is_distinct = False
        if ctx.oC_ProjectionBody().DISTINCT() is not None:
            is_distinct = True
        order_by_clause = self.order_by_clause
        skip_clause = self.skip_clause
        limit_clause = self.limit_clause
        self.return_clause = ReturnClause(projection_items, is_distinct, order_by_clause, skip_clause, limit_clause)

