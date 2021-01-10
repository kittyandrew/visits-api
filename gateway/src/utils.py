from sanic.response import json
import math


# TODO: Do json schema validation check with `jsonschema` - https://pypi.org/project/jsonschema
#       Missing keys -> early return with error
#       Extra keys (maybe allow some?) -> early return with error
def verify(ctx: dict, arg_name: str, exp_type, min_len = 0, max_len = math.inf):
    arg = ctx.get(arg_name)

    if not arg:
        return None, json(
            {
                "code": 2001,
                "argument": arg_name,
                "message": f"Missing {arg_name} argument (or is empty).",
            },
            status = 403
        )

    if not isinstance(arg, exp_type):
        return None, json(
            {
                "code": 2002,
                "argument": arg_name,
                "message": f"Incorrect type of \"{arg_name}\": expected \"{exp_type}\", got \"{type(arg)}\".",
            },
            status = 403
        )

    # TODO: here we assume arg is a string, and getting its length
    assert type(arg) is str
    if not(min_len < len(arg) < max_len):
        return None, json(
            {
                "code": 2003,
                "argument": arg_name,
                "message": f"Argument \"{arg_name}\" has limit in length! Got argument of length {len(arg)}, allowed range is {min_len}-{max_len}.",
            },
            status = 403
        )

    return arg, None
