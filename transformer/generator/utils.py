def convert_dict_to_str(input: dict[str,]) -> str:
    result = ""
    for key, value in input.items():
        result = result + key + ": "
        if value is None:
            result = result + "NULL"
        elif value.__class__ == str:
            result = result + value
        elif value.__class__ == dict:
            result = result + convert_dict_to_str(value)
        elif value.__class__ == list:
            result = result + convert_list_to_str(value)
        else:
            result = result + str(value)
        result = result + ", "
    return '{' + result.rstrip(", ") + '}'


def convert_list_to_str(input: list) -> str:
    result = '['
    for item in input:
        if item is None:
            result = result + "NULL"
        elif item.__class__ == str:
            result = result + item
        elif item.__class__ == dict:
            result = result + convert_dict_to_str(item)
        elif item.__class__ == list:
            result = result + convert_list_to_str(item)
        else:
            result = result + str(item)
        result = result + ", "
    return result.rstrip(", ") + ']'
