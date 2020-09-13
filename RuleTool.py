import argparse
from pathlib import Path


class KeyValue(argparse.Action):
    # Constructor calling
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, list())
        for value in values:
            # split it into key and value
            key, value = value.split("=")
            # assign into dictionary
            getattr(namespace, self.dest).append([key, value])


# Modular Functions
def extract_weight(prefix: str) -> float:
    if (prefix.find("<") > -1) and (prefix.find(">") > -1):
        weight_start = prefix.find("<") + 1
        weight_end = prefix.find(">")
        weight = prefix[weight_start:weight_end]
    else:
        weight = 0
    try:
        weight = float(weight)
    except ValueError:
        weight = 0
    return weight


def extract_sentence_cloud(prefix: str) -> str:
    if prefix.find("//") > -1:
        sentence_start = prefix.find("//") + 2
        return prefix[sentence_start:]


def enumerate_rules(file_text: str) -> dict:
    rule_start = file_text.find("(0:")
    rule_end = file_text.find("}", rule_start) + 1
    rule = file_text[rule_start:rule_end]
    rule_prefix = file_text[:rule_start]
    rule_prefixes = rule_prefix.split("\n")
    if rule_prefixes[-1].find("//") > -1:
        return {
            "text": None,
            "rule_end": rule_end
        }
    weight = extract_weight(rule_prefixes[-1])
    sentence_cloud = extract_sentence_cloud(rule_prefixes[-2])
    rule = {
        "text": rule,
        "weight": weight,
        "sentence_cloud": sentence_cloud,
        "rule_end": rule_end
    }
    return rule


def separate_rule_components(rule: dict) -> dict:
    original_texts = rule["text"].split("=>")
    rule["nodes"] = original_texts[0]
    if len(original_texts) > 1:
        rule["action"] = original_texts[1]
    else:
        rule["action"] = None
    return rule


def separate_action_components(rule: dict) -> dict:
    components = rule["action"]
    rule["actions_list"] = []
    components = components[2:-2]
    components = components.split(";")
    rule["actions_list"] = components
    return rule


def separate_action_subcomponents(rule: dict) -> dict:
    subcomponents_list = []
    for action in rule["actions_list"]:
        actions = action.split(".")
        if actions[0].find("AddProp") == -1:
            continue
        current_action = actions[1][:-1].split("=")
        subcomponents_list.append(current_action)
    rule["actions_dict"] = subcomponents_list
    return rule


def determine_requested_actions(rule: dict, requested_actions: list) -> bool:
    matches = 0
    for previous_action in rule["actions_dict"]:
        for requested_action in requested_actions:
            if previous_action[0] == requested_action[0] and previous_action[1] == requested_action[1]:
                matches += 1
                break
    if matches >= len(requested_actions):
        return True


# Procedural Functions
def read_file(file: str) -> str:
    if not (file and Path(file).is_file()):
        print("Invalid Path")
        exit(1)
    file_text = Path(file).read_text()
    return file_text


def extract_rule_metadata(file_text: str, requested_actions: list) -> list:
    rules = []
    while file_text.find("(0:") > -1:
        rule = enumerate_rules(file_text)
        file_text = file_text[rule["rule_end"]:]
        if not rule["text"]:
            continue
        rule = separate_rule_components(rule)
        if not rule["action"]:
            continue
        rule = separate_action_components(rule)
        rule = separate_action_subcomponents(rule)
        if not determine_requested_actions(rule, requested_actions):
            continue
        rules.append(rule)
    return rules


def reconstruct_rule(rule: dict) -> str:
    rule_text = ""
    if rule["sentence_cloud"]:
        rule_text += "//" + rule["sentence_cloud"] + "\n"
    if rule["weight"] != 0:
        rule_text += "<" + str(rule["weight"]) + "> "
    rule_text += rule["text"]
    return rule_text


def generate_output_file_name(requested_actions: list) -> str:
    name = "rules"
    for requested_action in requested_actions:
        name += "_" + requested_action[0] + "_" + requested_action[1]
    name += ".rls"
    return name


def write_file(rules: list, name: str, input_file: str):
    text = ""
    for rule in rules:
        rule_text = reconstruct_rule(rule)
        text += rule_text + "\n\n"
    file_path = Path(input_file).parent / name
    file_path.write_text(text)


def cleanup(rules: list, file_path: list, cc: bool, x: bool):
    input_path = Path(file_path[0])
    if x:
        input_path.write_text("#include " + file_path[1] + "\n\n" + input_path.read_text())
    if cc:
        file_text = input_path.read_text()
        for rule in rules:
            rule_text = reconstruct_rule(rule)
            file_text = file_text.replace(rule_text, "")
            input_path.write_text(file_text)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("input", metavar="input_file_path", type=str, help="Path of input rule set file for "
                                                                               "examination.")
    arg_parser.add_argument("--actions", required=True, nargs="*", action=KeyValue, help="hi")
    arg_parser.add_argument("-cc", action="store_true", help="")
    arg_parser.add_argument("-x", action="store_true", help="")

    args = arg_parser.parse_args()
    txt = read_file(args.input)
    output_ruleset = extract_rule_metadata(txt, args.actions)
    file_name = generate_output_file_name(args.actions)
    write_file(output_ruleset, file_name, args.input)
    cleanup(output_ruleset, [args.input, file_name], args.cc, args.x)
