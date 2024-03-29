import datetime
import os
from datetime import date, timedelta, datetime
from unittest import TestCase

import numpy as np
import pandas as pd

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestIS(TestCase):
    graphdb_connector = None
    products = None
    start_times = None
    start_persons = None
    TPS = {}
    RT = {}
    # 是否在已拓展的数据集上查询
    is_expanded = True
    # 是否在验证
    is_asserting = True
    root = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.graphdb_connector = GraphDBConnector()
        cls.graphdb_connector.default_connect()
        pd.set_option('display.max_columns', None)
        seed = 2024
        np.random.seed(seed)
        test_size = 50
        customer_df = pd.read_csv("../dataset/amazon/amazon-customer.csv", header=None, dtype=str)[[1]].dropna()
        product_df = pd.read_csv("../dataset/amazon/amazon-product.csv", header=None).fillna("NULL")[
            [1, 2, 3, 4, 5, 6, 7, 8]]
        cls.start_persons = customer_df.sample(test_size, random_state=seed)[1].values.tolist()
        cls.products = product_df.sample(test_size, random_state=seed)[1].values.tolist()
        # 限制时间范围[start_time, start_time + duration]
        # 开始时间范围：[1995-01-01, 2000-01-01]
        durations = np.random.randint(0, (date(2000, 1, 1) - date(1995, 1, 1)).days, test_size)
        cls.start_times = [date(1995, 1, 1) + timedelta(days=int(duration)) for duration in durations]
        # 持续时间范围：[0, 6years]
        durations = np.random.randint(0, 6 * 365, test_size)
        # 结束时间范围：[1995-01-01, 2006-01-01]
        cls.end_times = [start_time + timedelta(days=int(durations[index])) for index, start_time in
                         enumerate(cls.start_times)]
        if cls.is_expanded:
            cls.root = os.path.join("results", "expanded")
        else:
            cls.root = os.path.join("results", "original")

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.graphdb_connector.close()
        if cls.is_asserting:
            cls.TPS["AVG"] = np.mean(list(cls.TPS.values()))
            cls.RT["AVG"] = np.mean(list(cls.RT.values()))
            results = pd.DataFrame.from_dict({"TPS": cls.TPS, "RT": cls.RT})
            results.to_csv(os.path.join(cls.root, "IS_results.csv"))

    # 查询在[t1,t2]期间内注册的顾客
    def test_IS_1(self):
        if self.is_asserting:
            result_df = pd.read_csv(os.path.join(self.root, "IS", "IS_1_records.csv"), index_col=[0])
            total_record = []
            response_time = timedelta()
        else:
            result_df = pd.DataFrame()
        for index, start_time in enumerate(self.start_times):
            start_time = start_time.strftime("\"%Y-%m-%d\"")
            end_time = self.end_times[index].strftime("\"%Y-%m-%d\"")
            s_cypher = "MATCH (n:Customer) " + \
                       "WHERE n@T.from DURING interval(" + start_time + ", " + end_time + ") " + \
                       "RETURN n.id as customer"
            start_time = datetime.now()
            cypher_query = STransformer.transform(s_cypher)
            records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
            if self.is_asserting:
                response_time += datetime.now() - start_time
                total_record.extend(records)
            else:
                record_df = pd.DataFrame(records, columns=keys)
                result_df = pd.concat([result_df, record_df])
        if self.is_asserting:
            assert total_record == result_df.to_dict("records")
            response_time = response_time.total_seconds()
            self.TPS["IS_1"] = len(self.start_persons) / response_time
            self.RT["IS_1"] = response_time / len(self.start_persons)
        else:
            result_df.to_csv(os.path.join(self.root, "IS", "IS_1_records.csv"))

    # 某人的最新评论，返回最后10条评论，并返回评论的商品，以及该商品的标签
    def test_IS_2(self):
        if self.is_asserting:
            result_df = pd.read_csv(os.path.join(self.root, "IS", "IS_2_records.csv"), index_col=[0, 1])
            start_persons = [index[0] for index in result_df.index.values]
            response_time = timedelta()
        else:
            result_df = pd.DataFrame()
        for start_person in self.start_persons:
            s_cypher = "MATCH (n:Customer{id: \"" + start_person + "\"})-[:creatorOf]->(re:Review)<-[:containerOf]-(p:Product) " + \
                       "MATCH (p)-[:hasTag]->(t:Tag)" \
                       "RETURN re.rating as rating, re.votes as votes, p.id as product, t.name as tag " \
                       "ORDER BY re@T.from ASC LIMIT 10"
            start_time = datetime.now()
            cypher_query = STransformer.transform(s_cypher)
            records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
            if self.is_asserting:
                response_time += datetime.now() - start_time
                if start_person in start_persons:
                    assert records == result_df.loc[start_person].to_dict("records")
                else:
                    assert records == []
            else:
                record_df = pd.DataFrame(records, index=[np.full(len(records), start_person), np.arange(len(records))],
                                         columns=keys)
                result_df = pd.concat([result_df, record_df])
        if self.is_asserting:
            response_time = response_time.total_seconds()
            self.TPS["IS_2"] = len(self.start_persons) / response_time
            self.RT["IS_2"] = response_time / len(self.start_persons)
        else:
            result_df.to_csv(os.path.join(self.root, "IS", "IS_2_records.csv"))

    # 某人的所有朋友，以及他们成为朋友的日期
    def test_IS_3(self):
        if self.is_asserting:
            result_df = pd.read_csv(os.path.join(self.root, "IS", "IS_3_records.csv"), index_col=[0, 1])
            result_df["datetime"] = result_df["datetime"].apply(
                lambda dt: datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%f000%z"))
            start_persons = [index[0] for index in result_df.index.values]
            response_time = timedelta()
        else:
            result_df = pd.DataFrame()
        for start_person in self.start_persons:
            s_cypher = "MATCH (n:Customer{id: \"" + start_person + "\"})-[e:knows]->(m:Customer) " + \
                       "RETURN m.id as friend, e@T.from as datetime"
            start_time = datetime.now()
            cypher_query = STransformer.transform(s_cypher)
            records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
            if self.is_asserting:
                response_time += datetime.now() - start_time
                if start_person in start_persons:
                    assert records == result_df.loc[start_person].to_dict("records")
                else:
                    assert records == []
            else:
                record_df = pd.DataFrame(records, index=[np.full(len(records), start_person), np.arange(len(records))],
                                         columns=keys)
                result_df = pd.concat([result_df, record_df])
        if self.is_asserting:
            response_time = response_time.total_seconds()
            self.TPS["IS_3"] = len(self.start_persons) / response_time
            self.RT["IS_3"] = response_time / len(self.start_persons)
        else:
            result_df.to_csv(os.path.join(self.root, "IS", "IS_3_records.csv"))

    # 某商品的标题和创建日期
    def test_IS_4(self):
        if self.is_asserting:
            result_df = pd.read_csv(os.path.join(self.root, "IS", "IS_4_records.csv"), index_col=[0, 1])
            result_df["createTime"] = result_df["createTime"].apply(
                lambda dt: datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%f000%z"))
            products = [index[0] for index in result_df.index.values]
            response_time = timedelta()
        else:
            result_df = pd.DataFrame()
        for product in self.products:
            s_cypher = "MATCH (p:Product{id: " + str(product) + "}) " + \
                       "RETURN p.id as id, p.title as title, p@T.from as createTime"
            start_time = datetime.now()
            cypher_query = STransformer.transform(s_cypher)
            records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
            if self.is_asserting:
                response_time += datetime.now() - start_time
                if product in products:
                    assert records == result_df.loc[product].to_dict("records")
                else:
                    assert records == []
            else:
                record_df = pd.DataFrame(records, index=[np.full(len(records), product), np.arange(len(records))],
                                         columns=keys)
                result_df = pd.concat([result_df, record_df])
        if self.is_asserting:
            response_time = response_time.total_seconds()
            self.TPS["IS_4"] = len(self.start_persons) / response_time
            self.RT["IS_4"] = response_time / len(self.start_persons)
        else:
            result_df.to_csv(os.path.join(self.root, "IS", "IS_4_records.csv"))

    # 某商品的标签
    def test_IS_5(self):
        if self.is_asserting:
            result_df = pd.read_csv(os.path.join(self.root, "IS", "IS_5_records.csv"), index_col=[0, 1])
            products = [index[0] for index in result_df.index.values]
            response_time = timedelta()
        else:
            result_df = pd.DataFrame()
        for product in self.products:
            s_cypher = "MATCH (p:Product{id: " + str(product) + "})-[:hasTag]->(t:Tag) " + \
                       "RETURN p.id as product, t.name as tag"
            start_time = datetime.now()
            cypher_query = STransformer.transform(s_cypher)
            records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
            if self.is_asserting:
                response_time += datetime.now() - start_time
                if product in products:
                    assert records == result_df.loc[product].to_dict("records")
                else:
                    assert records == []
            else:
                record_df = pd.DataFrame(records, index=[np.full(len(records), product), np.arange(len(records))],
                                         columns=keys)
                result_df = pd.concat([result_df, record_df])
        if self.is_asserting:
            response_time = response_time.total_seconds()
            self.TPS["IS_5"] = len(self.start_persons) / response_time
            self.RT["IS_5"] = response_time / len(self.start_persons)
        else:
            result_df.to_csv(os.path.join(self.root, "IS", "IS_5_records.csv"))

    # 某商品的评论以及发布评论的顾客
    def test_IS_6(self):
        if self.is_asserting:
            result_df = pd.read_csv(os.path.join(self.root, "IS", "IS_6_records.csv"), index_col=[0, 1])
            products = [index[0] for index in result_df.index.values]
            response_time = timedelta()
        else:
            result_df = pd.DataFrame()
        for product in self.products:
            s_cypher = "MATCH (p:Product{id: " + str(
                product) + "})-[:containerOf]->(re:Review)<-[:creatorOf]-(n:Customer) " + \
                       "RETURN p.id as product, re.rating as rating, n.id as customer"
            start_time = datetime.now()
            cypher_query = STransformer.transform(s_cypher)
            records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
            if self.is_asserting:
                response_time += datetime.now() - start_time
                if product in products:
                    assert records == result_df.loc[product].to_dict("records")
                else:
                    assert records == []
            else:
                record_df = pd.DataFrame(records, index=[np.full(len(records), product), np.arange(len(records))],
                                         columns=keys)
                result_df = pd.concat([result_df, record_df])
        if self.is_asserting:
            response_time = response_time.total_seconds()
            self.TPS["IS_6"] = len(self.start_persons) / response_time
            self.RT["IS_6"] = response_time / len(self.start_persons)
        else:
            result_df.to_csv(os.path.join(self.root, "IS", "IS_6_records.csv"))

    # 某商品的共同购买商品，以及返回两个商品的购买者之间是否有认识的人
    def test_IS_7(self):
        if self.is_asserting:
            result_df = pd.read_csv(os.path.join(self.root, "IS", "IS_7_records.csv"), index_col=[0, 1])
            products = [index[0] for index in result_df.index.values]
            response_time = timedelta()
        else:
            result_df = pd.DataFrame()
        for product in self.products:
            s_cypher = "MATCH (p1:Product{id: " + str(product) + "})-[:CoPurchases]->(p2:Product) " + \
                       "OPTIONAL MATCH (p1)<-[:purchases]-(n:Customer)-[:purchases]->(p2)" \
                       "RETURN p1.id as product1, p2.id as product2, count(n) as coCustomer"
            start_time = datetime.now()
            cypher_query = STransformer.transform(s_cypher)
            records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
            if self.is_asserting:
                response_time += datetime.now() - start_time
                if product in products:
                    assert records == result_df.loc[product].to_dict("records")
                else:
                    assert records == []
            else:
                record_df = pd.DataFrame(records, index=[np.full(len(records), product), np.arange(len(records))],
                                         columns=keys)
                result_df = pd.concat([result_df, record_df])
        if self.is_asserting:
            response_time = response_time.total_seconds()
            self.TPS["IS_7"] = len(self.start_persons) / response_time
            self.RT["IS_7"] = response_time / len(self.start_persons)
        else:
            result_df.to_csv(os.path.join(self.root, "IS", "IS_7_records.csv"))
