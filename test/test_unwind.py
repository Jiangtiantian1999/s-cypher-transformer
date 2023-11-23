from textwrap import dedent
from unittest import TestCase

from transformer.s_transformer import STransformer


class TestUnwind(TestCase):
    def test_unwind_1(self):
        s_cypher = dedent("""
        UNWIND [1, 2, 3] AS x
        RETURN x
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_1:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_2(self):
        s_cypher = dedent("""
        WITH [1, 1, 2, 2] AS coll
        UNWIND coll AS x
        WITH DISTINCT x
        RETURN collect(x) AS SET
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_2:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_3(self):
        s_cypher = dedent("""
        UNWIND [
        datetime('2015-07-21T21:40:32.142+0100'),
        datetime('2015-W30-2T214032.142Z'),
        datetime('2015T214032-0100'),
        datetime('20150721T21:40-01:30'),
        datetime('2015-W30T2140-02'),
        datetime('2015202T21+18:00'),
        datetime('2015-07-21T21:40:32.142[Europe/London]'),
        datetime('2015-07-21T21:40:32.142-04[America/New_York]')
        ] AS theDate
        RETURN theDate;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("tset_unwind_3:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_4(self):
        s_cypher = dedent("""
        UNWIND [
        duration("P14DT16H12M"),
        duration("P5M1.5D"),
        duration("P0.75M"),
        duration("PT0.75M"),
        duration("P2012-02-02T14:37:21.545")
        ] AS aDuration
        RETURN aDuration;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_4:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_5(self):
        s_cypher = dedent("""
        UNWIND [
        duration({days: 14, hours:16, minutes: 12}),
        duration({months: 5, days: 1.5}),
        duration({months: 0.75}),
        duration({weeks: 2.5}),
        duration({minutes: 1.5, seconds: 1, milliseconds: 123, microseconds: 456, nanoseconds: 789}),
        duration({minutes: 1.5, seconds: 1, nanoseconds: 123456789})
        ] AS aDuration
        RETURN aDuration;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_5:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_6(self):
        s_cypher = dedent("""
        UNWIND [
        datetime({year: 1984, month: 10, day: 11, hour: 12, minute: 31, second: 14, millisecond: 123, microsecond: 456, nanosecond: 789}),
        datetime({year: 1984, month: 10, day: 11, hour: 12, minute: 31, second: 14, millisecond: 645, timezone: '+01:00'}),
        datetime({year: 1984, month: 10, day: 11, hour: 12, minute: 31, second: 14, nanosecond: 645876123, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, month: 10, day: 11, hour: 12, minute: 31, second: 14, timezone: '+01:00'}),
        datetime({year: 1984, month: 10, day: 11, hour: 12, minute: 31, second: 14}),
        datetime({year: 1984, month: 10, day: 11, hour: 12, minute: 31, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, month: 10, day: 11, hour: 12, timezone: '+01:00'}),
        datetime({year: 1984, month: 10, day: 11, timezone: 'Europe/Stockholm'})
        ] AS theDate
        RETURN theDate;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_6:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_7(self):
        s_cypher = dedent("""
        UNWIND [
        datetime({year: 1984, week: 10, dayOfWeek: 3, hour: 12, minute: 31, second: 14, millisecond: 645}),
        datetime({year: 1984, week: 10, dayOfWeek: 3, hour: 12, minute: 31, second: 14, microsecond: 645876, timezone: '+01:00'}),
        datetime({year: 1984, week: 10, dayOfWeek: 3, hour: 12, minute: 31, second: 14, nanosecond: 645876123, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, week: 10, dayOfWeek: 3, hour: 12, minute: 31, second: 14, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, week: 10, dayOfWeek: 3, hour: 12, minute: 31, second: 14}),
        datetime({year: 1984, week: 10, dayOfWeek: 3, hour: 12, timezone: '+01:00'}),
        datetime({year: 1984, week: 10, dayOfWeek: 3, timezone: 'Europe/Stockholm'})
        ] AS theDate
        RETURN theDate;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_7:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_8(self):
        s_cypher = dedent("""
        UNWIND [
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45, hour: 12, minute: 31, second: 14, microsecond: 645876}),
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45, hour: 12, minute: 31, second: 14, timezone: '+01:00'}),
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45, hour: 12, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45})
        ] AS theDate
        RETURN theDate;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_8:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_9(self):
        s_cypher = dedent("""
        UNWIND [
        datetime({year: 1984, ordinalDay: 202, hour: 12, minute: 31, second: 14, millisecond: 645}),
        datetime({year: 1984, ordinalDay: 202, hour: 12, minute: 31, second: 14, timezone: '+01:00'}),
        datetime({year: 1984, ordinalDay: 202, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, ordinalDay: 202})
        ] AS theDate
        RETURN theDate
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_unwind_9:", s_cypher, '\n', cypher_query, '\n')
