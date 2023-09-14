import unittest

from antlr4 import *
from transformer.generator.cypher_generator import CypherGenerator
from transformer.grammar_parser.s_cypherLexer import s_cypherLexer
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.main import transform_to_cypher
from transformer.translator.cypher_translator import CypherTranslator
from unittest import TestCase, TestSuite, TextTestRunner


class TestMain(TestCase):
    def test_match_1(self):
        cypher_query = transform_to_cypher(
            'MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})'
            'RETURN n;')
        print("test_match_1--------------")
        print(cypher_query)

    def test_match_2(self):
        cypher_query = transform_to_cypher('MATCH (n:City@T("1690", NOW) )'
                                           'RETURN n;')
        print("test_match_2--------------")
        print(cypher_query)


if __name__ == '__main__':
    match_suite = TestSuite()
    match_suite.addTest(TestMain('test_match_1'))
    match_suite.addTest(TestMain('test_match_2'))

    runner = TextTestRunner()
    runner.run(match_suite)
