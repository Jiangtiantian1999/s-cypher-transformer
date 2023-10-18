import json
import os


class GlobalVariables:

    @staticmethod
    def get_function_info():
        with open(os.path.join(os.path.dirname(__file__), "conf\\function_info.json"), "r") as file:
            function_info_dir = json.load(file)
            scypher_function_info = function_info_dir["scypher"]
            cypher_function_info = function_info_dir["cypher"]
            function_info = scypher_function_info.copy()
            function_info.update(cypher_function_info)
            return scypher_function_info, cypher_function_info, function_info

    @staticmethod
    def get_procedure_info():
        with open(os.path.join(os.path.dirname(__file__), "conf\\procedure_info.json"), "r") as file:
            procedure_info_dir = json.load(file)
            scypher_procedure_info = procedure_info_dir["scypher"]
            cypher_procedure_info = procedure_info_dir["cypher"]
            procedure_info = scypher_procedure_info.copy()
            procedure_info.update(cypher_procedure_info)
            return scypher_procedure_info, cypher_procedure_info, procedure_info

    scypher_function_info, cypher_function_info, function_info = get_function_info()
    scypher_procedure_info, cypher_procedure_info, procedure_info = get_procedure_info()
