import argparse
from pathlib import Path


# Modular Functions
def extract_weight(prefix: str) -> float:
    if (prefix.find("<") > -1) and (prefix.find(">") > -1):
        weight_start = prefix.find("<") + 1
        weight_end = prefix.find(">")
        weight = prefix[weight_start:weight_end]
    else:
        weight = 1.0
    # try:
    weight = float(weight)
    # except ValueError:
    # weight = 1.0
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


def select_requested_rules(original_ruleset: list) -> list:
    new_ruleset = []
    for original_rule in original_ruleset:
        original_texts = original_rule["text"].split("=>")
        original_rule["nodes"] = original_texts[0]
        if len(original_texts) > 1:
            original_rule["action"] = original_texts[1]
        else:
            original_rule["action"] = None
        new_ruleset.append(original_rule)
    return new_ruleset


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("input", metavar="input_file_path", type=str, help="Path of input rule set file for "
                                                                           "examination.")
    args = parser.parse_args()
    txt = read_file(args.input)
    all_rules = enumerate_rules(txt)
    selected_rules = select_requested_rules(all_rules)
    print(selected_rules)
