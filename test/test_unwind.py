from datetime import timezone
from unittest import TestCase

import pytz
from neo4j.time import Duration, DateTime

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestUnwind(TestCase):
    graphdb_connector = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.graphdb_connector = GraphDBConnector()
        cls.graphdb_connector.out_net_connect()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.graphdb_connector.close()

    def test_unwind(self):
        s_cypher = """
        UNWIND [1, 2, 3] AS x
        RETURN x
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"x": 1}, {"x": 2}, {"x": 3}]

        s_cypher = """
        WITH [1, 1, 2, 2] AS coll
        UNWIND coll AS x
        WITH DISTINCT x
        RETURN collect(x) AS result
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"result": [1, 2]}]

    def test_unwind_duration(self):
        s_cypher = """
        UNWIND [
        duration("P14DT16H12M"),
        duration("P5M1.5D"),
        duration("P0.75M"),
        duration("PT0.75M"),
        duration("P2012-02-02T14:37:21.545")
        ] AS aDuration
        RETURN aDuration;
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"aDuration": Duration(days=14, hours=16, minutes=12)},
                           {"aDuration": Duration(months=5, days=1, hours=12)},
                           {"aDuration": Duration(days=22, hours=19, minutes=51, seconds=49, nanoseconds=500000000)},
                           {"aDuration": Duration(minutes=0.75)},
                           {"aDuration": Duration(years=2012, months=2, days=2, hours=14, minutes=37, seconds=21.545)}]

        s_cypher = """
        UNWIND [
        duration({days: 14, hours:16, minutes: 12}),
        duration({months: 5, days: 1.5}),
        duration({months: 0.75}),
        duration({weeks: 2.5}),
        duration({minutes: 1.5, seconds: 1, milliseconds: 123, microseconds: 456, nanoseconds: 789}),
        duration({minutes: 1.5, seconds: 1, nanoseconds: 123456789})
        ] AS aDuration
        RETURN aDuration;
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"aDuration": Duration(days=14, hours=16, minutes=12)},
            {"aDuration": Duration(months=5, days=1, hours=12)},
            {"aDuration": Duration(days=22, hours=19, minutes=51, seconds=49, nanoseconds=500000000)},
            {"aDuration": Duration(weeks=2, days=3, hours=12)},
            {"aDuration": Duration(minutes=1.5, seconds=1, milliseconds=123, microseconds=456, nanoseconds=789)},
            {"aDuration": Duration(minutes=1.5, seconds=1, nanoseconds=123456789)}]

    def test_unwind_datetime(self):
        s_cypher = """
        UNWIND [
        datetime('2015-07-21T21:40:32.142+0100'),
        datetime('2015-W30-2T214032.142Z'),
        datetime('2015T214032-0100'),
        datetime('20150721T21:40-01:30'),
        datetime('2015-W30T2140-02'),
        datetime('2015202T21+18:00')
        ] AS theDate
        RETURN theDate;
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"aDuration": DateTime(year=2015, month=7, day=21, hour=21, minute=40, second=32, nanosecond=142000000,
                                   tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=2015, month=7, day=21, hour=21, minute=40, second=32, nanosecond=142000000,
                                   tzinfo=timezone.utc)},
            {"aDuration": DateTime(year=2015, month=1, day=1, hour=21, minute=40, second=32,
                                   tzinfo=pytz.FixedOffset(-60))},
            {"aDuration": DateTime(year=2015, month=7, day=21, hour=21, minute=40, tzinfo=pytz.FixedOffset(-90))},
            {"aDuration": DateTime(year=2015, month=7, day=20, hour=21, minute=40, tzinfo=pytz.FixedOffset(-120))},
            {"aDuration": DateTime(year=2015, month=7, day=21, hour=21, tzinfo=pytz.FixedOffset(+1080))}]

        s_cypher = """
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
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"aDuration": DateTime(year=1984, month=10, day=11, hour=12, minute=31, second=14, nanosecond=123456789)},
            {"aDuration": DateTime(year=1984, month=10, day=11, hour=12, minute=31, second=14, nanosecond=645000000,
                                   tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=1984, month=10, day=11, hour=12, minute=31, second=14, nanosecond=645876123,
                                   tzinfo=pytz.timezone("Europe/Stockholm"))},
            {"aDuration": DateTime(year=1984, month=10, day=11, hour=12, minute=31, second=14,
                                   tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=1984, month=10, day=11, hour=12, minute=31, second=14, tzinfo=timezone.utc)},
            {"aDuration": DateTime(year=1984, month=10, day=11, hour=12, minute=31,
                                   tzinfo=pytz.timezone("Europe/Stockholm"))},
            {"aDuration": DateTime(year=1984, month=10, day=11, tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=1984, month=10, day=11, tzinfo=pytz.timezone("Europe/Stockholm"))}]

        s_cypher = """
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
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"aDuration": DateTime(year=1984, month=3, day=7, hour=12, minute=31, second=14, nanosecond=645000000)},
            {"aDuration": DateTime(year=1984, month=3, day=7, hour=12, minute=31, second=14, nanosecond=645876000,
                                   tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=1984, month=3, day=7, hour=12, minute=31, second=14, nanosecond=645876123,
                                   tzinfo=pytz.timezone("Europe/Stockholm"))},
            {"aDuration": DateTime(year=1984, month=3, day=7, hour=12, minute=31, second=14,
                                   tzinfo=pytz.timezone("Europe/Stockholm"))},
            {"aDuration": DateTime(year=1984, month=3, day=7, hour=12, minute=31, second=14, tzinfo=timezone.utc)},
            {"aDuration": DateTime(year=1984, month=3, day=7, hour=12, tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=1984, month=3, day=7, tzinfo=pytz.timezone("Europe/Stockholm"))}]

        s_cypher = """
        UNWIND [
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45, hour: 12, minute: 31, second: 14, microsecond: 645876}),
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45, hour: 12, minute: 31, second: 14, timezone: '+01:00'}),
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45, hour: 12, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, quarter: 3, dayOfQuarter: 45})
        ] AS theDate
        RETURN theDate;
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"aDuration": DateTime(year=1984, month=8, day=14, hour=12, minute=31, second=14, nanosecond=645876000,
                                   tzinfo=timezone.utc)},
            {"aDuration": DateTime(year=1984, month=8, day=14, hour=12, minute=31, second=14, nanosecond=645876123,
                                   tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=1984, month=8, day=14, hour=12, tzinfo=pytz.timezone("Europe/Stockholm"))},
            {"aDuration": DateTime(year=1984, month=8, day=14, tzinfo=timezone.utc)}]

        s_cypher = """
        UNWIND [
        datetime({year: 1984, ordinalDay: 202, hour: 12, minute: 31, second: 14, millisecond: 645}),
        datetime({year: 1984, ordinalDay: 202, hour: 12, minute: 31, second: 14, timezone: '+01:00'}),
        datetime({year: 1984, ordinalDay: 202, timezone: 'Europe/Stockholm'}),
        datetime({year: 1984, ordinalDay: 202})
        ] AS theDate
        RETURN theDate
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"aDuration": DateTime(year=1984, month=7, day=20, hour=12, minute=31, second=14, nanosecond=645000000,
                                   tzinfo=timezone.utc)},
            {"aDuration": DateTime(year=1984, month=7, day=20, hour=12, minute=31, second=14,
                                   tzinfo=pytz.FixedOffset(60))},
            {"aDuration": DateTime(year=1984, month=7, day=20, hour=12, tzinfo=pytz.timezone("Europe/Stockholm"))},
            {"aDuration": DateTime(year=1984, month=7, day=20, tzinfo=timezone.utc)}]
