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
    root_element: str,
    items: list[dict[str, Any]],
    filters: list[dict[str, Any]],
) -> dict[str, Any]:

    matches = []

    for item in items:

        matched = True

        for filter_definition in filters:

            current = item

            path_parts = filter_definition["MatchPath"].split(".")
            match_values = filter_definition["MatchValues"]

            for part in path_parts:
                if not isinstance(current, dict):
                    current = None
                    break

                current = current.get(part)

                if current is None:
                    break

            if current not in match_values:
                matched = False
                break

        if matched:
            matches.append(item)

    return {
        root_element: matches
    }

def retrieve_candidate_configuration(
    yaml_file_path: str,
    root_element: str,
    filters: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    with Path(yaml_file_path).open(
        "r",
        encoding="utf-8",
    ) as file:
        configuration = yaml.safe_load(file)

    items = configuration.get(root_element, [])

    return filter_items(
        root_element=root_element,
        items=items,
        filters=filters,
    )

# Profiles example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/profiles.yaml"
paper_profile = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="Profiles",

    filters=[
        {
            "MatchPath": "Profile.Name",
            "MatchValues": [
                "asyafoek-stocks-long-swing-paper",
            ]
        }
    ]
)
print(f"Config Profiles\n{to_yaml(paper_profile)}\n")

# RiskReward example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/riskreward.yaml"
paper_riskreward = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="RiskRewardNotations",
    filters=[
        {
            "MatchPath": "ProfileName",
            "MatchValues": [
                "asyafoek-stocks-long-swing-paper",
            ],
        },
        {
            "MatchPath": "TrendRegime",
            "MatchValues": [
                "BEARISH",
            ],
        },
        {
            "MatchPath": "VolatilityRegime",
            "MatchValues": [
                "QUIET",
            ],
        }
    ],
)
print(f"Config RiskReward\n{to_yaml(paper_riskreward)}\n")


# RuleProviders example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/reference-data/rule_providers.yaml"
paper_ruleproviders = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="RuleProviders",
    filters=[
        {
            "MatchPath": "EngineVersion",
            "MatchValues": [1],
        }
    ],
)
print(f"Config RuleProviders\n{to_yaml(paper_ruleproviders)}\n")

# Current Classification example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/tradeclassifications.yaml"
current_classification = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="TradeClassifications",
    filters=[
        {
            "MatchPath": "Classification",
            "MatchValues": [
                "GoodLoss",
            ],
        }
    ],
)
print(f"Current Classification\n{to_yaml(current_classification)}\n")

# Target Classification example
filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/tradeclassifications.yaml"
target_classification = retrieve_candidate_configuration(
    yaml_file_path=filename,
    root_element="TradeClassifications",
    filters=[
        {
            "MatchPath": "Classification",
            "MatchValues": [
                "GoodProfit",
            ],
        }
    ],
)
print(f"Target Classification\n{to_yaml(target_classification)}\n")

