from __future__ import annotations

from typing import List

from transformer.exceptions.s_exception import ClauseError
from transformer.ir.s_clause_component import Pattern, Expression, ProjectionItem
from transformer.ir.s_datetime import TimePoint, Interval


class Clause:
    time_granularity = TimePoint.LOCALDATETIME


# 读查询，包括Match子句，Unwind子句和Call子句
class ReadingClause(Clause):
    def get_variables(self):
        return []


class WhereClause(Clause):
    def __init__(self, expression: Expression):
        self.expression = expression


class OrderByClause(Clause):
    def __init__(self, sort_items: dict[Expression, str]):
        self.sort_items = sort_items


class SkipClause(Clause):
    def __init__(self, expression: Expression):
        self.expression = expression


class LimitClause(Clause):
    def __init__(self, expression: Expression):
        self.expression = expression


class ReturnClause(Clause):
    def __init__(self, projection_items: List[ProjectionItem], is_distinct: bool = False,
                 order_by_clause: OrderByClause = None, skip_clause: SkipClause = None,
                 limit_clause: LimitClause = None):
        self.projection_items = projection_items
        self.is_distinct = is_distinct
        self.order_by_clause = order_by_clause
        self.skip_clause = skip_clause
        self.limit_clause = limit_clause


class MatchClause(ReadingClause):
    def __init__(self, patterns: List[Pattern] = None, is_optional: bool = False, where_clause: WhereClause = None,
                 time_window: TimePoint | Interval = None):
        self.patterns = patterns
        self.is_optional = is_optional
        self.where_clause = where_clause
        self.time_window = time_window

    def get_variables(self):
        variables = []
        for pattern in self.patterns:
            variables.extend(pattern.get_variables())
        return variables


class UnwindClause(ReadingClause):
    def get_variables(self):
        return []


class InnerCallClause(ReadingClause):
    def get_variables(self):
        return []


# 更新查询
class UpdatingClause(Clause):
    def get_variables(self):
        return []


# 最后的子句为return或update的查询模块，单一查询
class SingleQueryClause(Clause):
    def __init__(self, reading_clauses: List[ReadingClause] = None, updating_clauses: List[UpdatingClause] = None,
                 return_clause: ReadingClause = None):
        if reading_clauses is None:
            reading_clauses = []
        self.reading_clauses = reading_clauses
        if updating_clauses is None:
            updating_clauses = []
        self.updating_clauses = updating_clauses
        self.return_clause = return_clause

    def get_variables(self):
        variables = []
        for reading_clause in self.reading_clauses:
            variables.extend(reading_clause.get_variables())
        for updating_clause in self.updating_clauses:
            variables.extend(updating_clause.get_variables())
        return variables


class WithClause(Clause):
    def __init__(self, projection_items: List[ProjectionItem], is_distinct: bool = False,
                 order_by_clause: OrderByClause = None, skip_clause: SkipClause = None,
                 limit_clause: LimitClause = None):
        self.projection_items = projection_items
        self.is_distinct = is_distinct
        self.order_by_clause = order_by_clause
        self.skip_clause = skip_clause
        self.limit_clause = limit_clause


# 最后的子句为with的查询模块
class WithQueryClause(Clause):
    def __init__(self, with_clause: WithClause, reading_clauses: List[ReadingClause] = None,
                 updating_clauses: List[UpdatingClause] = None):
        self.with_clause = with_clause
        if reading_clauses is None:
            reading_clauses = []
        self.reading_clauses = reading_clauses
        if updating_clauses is None:
            updating_clauses = []
        self.updating_clauses = updating_clauses

    def get_variables(self):
        variables = []
        for reading_clause in self.reading_clauses:
            variables.extend(reading_clause.get_variables())
        for updating_clause in self.updating_clauses:
            variables.extend(updating_clause.get_variables())
        return variables


# 多个查询（用WITH子句连接）
class MultiQueryClause(Clause):
    def __init__(self, single_query_clause: SingleQueryClause = None, with_query_clauses: List[WithQueryClause] = None):
        # 最后的子句为return或update的查询模块
        self.single_query_clause = single_query_clause
        # 最后的子句为with的查询模块
        if with_query_clauses is None:
            with_query_clauses = []
        self.with_query_clauses = with_query_clauses

    def get_variables(self):
        variables = []
        for with_query_clause in self.with_query_clauses:
            variables.extend(with_query_clause.get_variables())
        variables.extend(self.single_query_clause.get_variables())
        return variables


# 复合查询（用UNION或UNION ALL连接）
class UnionQueryClause(Clause):
    def __init__(self, multi_query_clauses: List[MultiQueryClause], is_all: List[bool] = None):
        if is_all is None:
            is_all = []
        if len(multi_query_clauses) != len(is_all) + 1:
            raise ClauseError("The numbers of the clauses and union operations are not matched.")
        self.multi_query_clauses = multi_query_clauses
        self.is_all = is_all

    def get_variables(self):
        variables = []
        for multi_query_clause in self.multi_query_clauses:
            variables.extend(multi_query_clause.get_variables())
        return variables


# 独立的Call查询
class StandaloneCallClause(Clause):
    pass


# 时间窗口限定
class TimeWindowLimitClause(Clause):
    pass


class SCypherClause(Clause):
    def __init__(self, query_clause: UnionQueryClause | StandaloneCallClause | TimeWindowLimitClause):
        self.query_clause = query_clause

    def get_variables(self):
        if self.query_clause.__class__ == UnionQueryClause.__class__:
            return self.query_clause.get_variables()
        return []
