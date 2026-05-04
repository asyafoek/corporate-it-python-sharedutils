import json

def pretty_print(data):
    print(json.dumps(data, indent=2, sort_keys=True))
