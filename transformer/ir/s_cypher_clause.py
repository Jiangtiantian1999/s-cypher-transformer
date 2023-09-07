from typing import List

from transformer.exceptions.s_exception import ClauseError
from transformer.ir.s_clause_component import Pattern, ProjectionItem
from transformer.ir.s_datetime import TimePoint, Interval
from transformer.ir.s_expression import Expression


class Clause:
    time_granularity = TimePoint.LOCALDATETIME


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


class MatchClause():

    def __init__(self, patterns: List[Pattern], is_optional: bool = False, where_clause: WhereClause = None,
                 time_window: TimePoint | Interval = None):
        self.patterns = patterns
        self.is_optional = is_optional
        self.where_clause = where_clause
        self.time_window = time_window

    def get_variables_dict(self):
        variables_dict = {}
        for pattern in self.patterns:
            variables_dict.update(pattern.get_variables_dict())
        return variables_dict


class UnwindClause(Clause):
    def get_variables_dict(self):
        return {}

    pass


class YieldClause(Clause):
    def __init__(self, yield_items: dict[str, str], where_clause: WhereClause = None):
        self.yield_items = yield_items
        self.where_clause = where_clause

    def get_variables_dict(self):
        variables_dict = {}
        for key, value in self.yield_items:
            if value:
                variables_dict[value] = YieldClause
            else:
                variables_dict[key] = YieldClause


class CallClause(Clause):

    def __init__(self, procedure_name: str, input_items: List[Expression] = None, yield_clause: YieldClause = None):
        self.procedure_name = procedure_name
        self.input_items = input_items
        self.yield_clause = yield_clause

    def get_variables_dict(self):
        if self.yield_clause:
            return self.yield_clause.get_variables_dict()
        return {}


# 读查询
class ReadingClause(Clause):
    def __init__(self, reading_clause: MatchClause | UnwindClause | CallClause):
        self.reading_clause = reading_clause

    def get_variables_dict(self):
        return self.reading_clause.get_variables_dict()


# 更新查询
class UpdatingClause(Clause):
    def get_variables_dict(self):
        return {}

    pass


# 最后的子句为return或update的查询模块，单一查询
class SingleQueryClause(Clause):
    def __init__(self, reading_clauses: List[ReadingClause] = None, updating_clauses: List[UpdatingClause] = None,
                 return_clause: ReadingClause = None):
        if updating_clauses is None and return_clause is None:
            raise ClauseError("The updating_clauses and the return_clause can't be None at the same time.")
        if reading_clauses is None:
            reading_clauses = []
        self.reading_clauses = reading_clauses
        if updating_clauses is None:
            updating_clauses = []
        self.updating_clauses = updating_clauses
        self.return_clause = return_clause

    def get_variables_dict(self):
        variables_dict = []
        for reading_clause in self.reading_clauses:
            variables_dict.extend(reading_clause.get_variables_dict())
        for updating_clause in self.updating_clauses:
            variables_dict.extend(updating_clause.get_variables_dict())
        return variables_dict


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

    def get_variables_dict(self):
        variables_dict = {}
        for reading_clause in self.reading_clauses:
            variables_dict.update(reading_clause.get_variables_dict())
        for updating_clause in self.updating_clauses:
            variables_dict.update(updating_clause.get_variables_dict())
        return variables_dict


# 多个查询（用WITH子句连接）
class MultiQueryClause(Clause):
    def __init__(self, single_query_clause: SingleQueryClause, with_query_clauses: List[WithQueryClause] = None):
        # 最后的子句为return或update的查询模块
        self.single_query_clause = single_query_clause
        # 最后的子句为with的查询模块
        if with_query_clauses is None:
            with_query_clauses = []
        self.with_query_clauses = with_query_clauses

    def get_variables_dict(self):
        variables = {}
        for with_query_clause in self.with_query_clauses:
            variables.update(with_query_clause.get_variables_dict())
        variables.update(self.single_query_clause.get_variables_dict())
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

    def get_variables_dict(self):
        variables_dict = {}
        for multi_query_clause in self.multi_query_clauses:
            variables_dict.update(multi_query_clause.get_variables_dict())
        return variables_dict


# 时间窗口限定
class TimeWindowLimitClause(Clause):
    pass


class SCypherClause(Clause):
    def __init__(self, query_clause: UnionQueryClause | CallClause | TimeWindowLimitClause):
        self.query_clause = query_clause

    def get_variables_dict(self):
        if self.query_clause.__class__ in [UnionQueryClause.__class__, CallClause.__class__]:
            return self.query_clause.get_variables_dict()
        return {}
