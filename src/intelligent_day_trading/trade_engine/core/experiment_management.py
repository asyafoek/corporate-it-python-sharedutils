from pathlib import Path
from typing import Any

import yaml


def to_yaml(data: dict) -> str:
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )

def filter_items(
    items: list[dict[str, Any]],
    match_path: str,
    match_values: [str],
) -> list[dict[str, Any]]:
    """
    Filter items using a dot-separated path.

    Example:

        match_path  = "Profile.Name"
        match_value = "asyafoek-stocks-long-swing-paper"
    """

    path_parts = match_path.split(".")
    matches = []

    for item in items:
        current = item

        for part in path_parts:
            if not isinstance(current, dict):
                current = None
                break

            current = current.get(part)

            if current is None:
                break

        if current in match_values:
            matches.append(item)

    return matches


def retrieve_candidate_configuration(
    yaml_file_path: str,
    root_element: str,
    match_path: str,
    match_values: [str],
) -> list[dict[str, Any]]:
    """
    Example:

        retrieve_candidate_configuration(
            yaml_file_path="profiles.yaml",
            root_element="Profiles",
            match_path="Profile.Name",
            match_values=["asyafoek-stocks-long-swing-paper"],
        )

        retrieve_candidate_configuration(
            yaml_file_path="riskreward.yaml",
            root_element="RiskRewardNotations",
            match_path="ProfileName",
            match_values=[]"asyafoek-stocks-long-swing-paper"],
        )
    """

    with Path(yaml_file_path).open("r", encoding="utf-8") as file:
        configuration = yaml.safe_load(file)

    items = configuration.get(root_element, [])

    return {
        root_element: filter_items(
            items=items,
            match_path=match_path,
            match_values=match_values,
        )
    }


# Profiles example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/profiles.yaml"
paper_profile = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="Profiles",
    match_path="Profile.Name",
    match_values=["asyafoek-stocks-long-swing-paper"],
)
print("Config Profiles\n", to_yaml(paper_profile))

# RiskReward example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/riskreward.yaml"
paper_riskreward = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="RiskRewardNotations",
    match_path="ProfileName",
    match_values=["asyafoek-stocks-long-swing-paper"],
)
print("Config RiskReward\n", to_yaml(paper_riskreward))

# RuleProviders example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/reference-data/rule_providers.yaml"
paper_ruleproviders = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="RuleProviders",
    match_path="EngineVersion",
    match_values=[1],
)
print("Config RuleProviders\n", to_yaml(paper_ruleproviders))

# Current Classification example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/tradeclassifications.yaml"
current_classification = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="TradeClassifications",
    match_path="Classification",
    match_values=["GoodLoss"],
)
print("Current Classification\n", to_yaml(current_classification))

# Target Classification example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/tradeclassifications.yaml"
target_classification = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="TradeClassifications",
    match_path="Classification",
    match_values=["GoodProfit"],
)
print("Target Classification\n", to_yaml(target_classification))

