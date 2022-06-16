import yaml

with open("action.yml") as fh:
    data = yaml.safe_load(fh)

print(f"INPUTS = {data['inputs']}")
