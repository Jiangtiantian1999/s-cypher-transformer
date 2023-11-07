def convert_dict_to_str(mp: dict[str,]) -> str:
    result = ""
    for key, value in mp.items():
        result = result + key + ": "
        if value is None:
            result = result + "NULL"
        elif value.__class__ == str:
            result = result + value
        elif value.__class__ == dict:
            result = result + convert_dict_to_str(value)
        else:
            result = result + str(value)
        result = result + ", "
    return '{' + result.rstrip(", ") + '}'
