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


# Procedural Functions
def read_file(file: str) -> str:
    if not (file and Path(file).is_file()):
        print("Invalid Path")
        exit(1)
    file_text = Path(file).read_text()
    return file_text


def enumerate_rules(file_text: str):
    rules = []
    while file_text.find("(0:") > -1:
        rule_start = file_text.find("(0:")
        rule_end = file_text.find("}", rule_start) + 1
        rule = file_text[rule_start:rule_end]
        rule_prefix = file_text[:rule_start]
        rule_prefixes = rule_prefix.split("\n")
        if rule_prefixes[-1].find("//") > -1:
            file_text = file_text[rule_end:]
            continue
        weight = extract_weight(rule_prefixes[-1])
        sentence_cloud = extract_sentence_cloud(rule_prefixes[-2])
        rules.append({
            "text": rule,
            "weight": weight,
            "sentence_cloud": sentence_cloud
        })
        file_text = file_text[rule_end:]
    return rules


def separate_rule_components(previous_ruleset: list) -> list:
    updated_ruleset = []
    for previous_rule in previous_ruleset:
        original_texts = previous_rule["text"].split("=>")
        previous_rule["nodes"] = original_texts[0]
        if len(original_texts) > 1:
            previous_rule["action"] = original_texts[1]
        else:
            previous_rule["action"] = None
        updated_ruleset.append(previous_rule)
    return updated_ruleset


def separate_action_components(previous_ruleset: list) -> list:
    updated_ruleset = []
    for previous_rule in previous_ruleset:
        components = previous_rule["action"]
        previous_rule["actions_list"] = []
        if not components:
            continue
        components = components[2:-2]
        components = components.split(";")
        previous_rule["actions_list"] = components
        updated_ruleset.append(previous_rule)
    return updated_ruleset


def separate_action_subcomponents(previous_ruleset: list) -> list:
    updated_ruleset = []
    for previous_rule in previous_ruleset:
        subcomponents_list = []
        for previous_action in previous_rule["actions_list"]:
            previous_actions = previous_action.split(".")
            if previous_actions[0].find("AddProp") == -1 and previous_actions[0].find("RemoveProp") == -1:
                continue
            current_action = previous_actions[1][:-1].split("=")
            subcomponents_list.append(current_action)
        previous_rule["actions_dict"] = subcomponents_list
        updated_ruleset.append(previous_rule)
    return updated_ruleset


def select_requested_actions(previous_ruleset: list, requested_actions: list) -> list:
    updated_ruleset = []
    for previous_rule in previous_ruleset:
        matches = 0
        for previous_action in previous_rule["actions_dict"]:
            for requested_action in requested_actions:
                if previous_action[0] == requested_action[0] and previous_action[1] == requested_action[1]:
                    matches += 1
                    break
        if matches >= len(requested_actions):
            updated_ruleset.append(previous_rule)
    return updated_ruleset


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
    input_ruleset = enumerate_rules(txt)
    input_ruleset = separate_rule_components(input_ruleset)
    input_ruleset = separate_action_components(input_ruleset)
    input_ruleset = separate_action_subcomponents(input_ruleset)
    output_ruleset = select_requested_actions(input_ruleset, args.actions)
    file_name = generate_output_file_name(args.actions)
    write_file(output_ruleset, file_name, args.input)
    cleanup(output_ruleset, [args.input, file_name], args.cc, args.x)
