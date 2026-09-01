from __future__ import annotations
from copy import deepcopy
from typing import Any
from pathlib import Path
from jinja2 import Template
import requests
from typing import Literal
from copy import deepcopy

import os
import yaml

def from_yaml(file_path: Path) -> dict:
    configuration = None
    with Path(file_path).open(
        "r",
        encoding="utf-8",
    ) as file:
        configuration = yaml.safe_load(file)
    return configuration

class DoubleQuotedDumper(yaml.SafeDumper):
    pass


def str_presenter(dumper, data):
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str",
        data,
        style='"',
    )


DoubleQuotedDumper.add_representer(
    str,
    str_presenter,
)

def to_yaml(data: dict, useSafeDumper=True) -> str:
    if useSafeDumper:
        return yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
    else:
        return yaml.dump(
            data,
            Dumper=DoubleQuotedDumper,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )



def _find_matching_item(
    items: list[dict[str, Any]],
    filters: list[dict[str, Any]],
) -> tuple[int | None, dict[str, Any] | None]:

    for index, item in enumerate(items):

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
            return index, item

    return None, None


def update_yaml_array_item(
    yaml_data: dict[str, Any],
    root_element: str,
    filters: list[dict[str, Any]],
    updates: dict[str, Any],
) -> dict[str, Any]:

    result = deepcopy(yaml_data)

    items = result[root_element]

    if not isinstance(items, list):
        raise ValueError(f"{root_element} is not a list")

    _, item = _find_matching_item(
        items=items,
        filters=filters,
    )

    if item is None:
        raise ValueError("No matching item found")

    _deep_merge(
        target=item,
        source=updates,
    )

    return result


def overwrite_yaml_array_item(
    yaml_data: dict[str, Any],
    root_element: str,
    filters: list[dict[str, Any]],
    item: dict[str, Any],
) -> dict[str, Any]:

    result = deepcopy(yaml_data)

    items = result[root_element]

    if not isinstance(items, list):
        raise ValueError(f"{root_element} is not a list")

    index, _ = _find_matching_item(
        items=items,
        filters=filters,
    )

    if index is None:
        raise ValueError("No matching item found")

    items[index] = deepcopy(item)

    return result



def upsert_yaml_array_item(
    yaml_data: dict[str, Any],
    root_element: str,
    filters: list[dict[str, Any]],
    item: dict[str, Any],
) -> dict[str, Any]:

    result = deepcopy(yaml_data)

    items = result[root_element]

    if not isinstance(items, list):
        raise ValueError(f"{root_element} is not a list")

    _, existing_item = _find_matching_item(
        items=items,
        filters=filters,
    )

    if existing_item is not None:

        _deep_merge(
            target=existing_item,
            source=item,
        )            

    else:
        items.append(deepcopy(item))

    return result


def _deep_merge(
    target: dict[str, Any],
    source: dict[str, Any],
) -> None:
    for key, value in source.items():

        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(target[key], value)
        else:
            target[key] = deepcopy(value)


def merge_yaml_array_item(
    yaml_data: dict[str, Any],
    root_element: str,
    filters: list[dict[str, Any]],
    data: dict[str, Any],
    operation: Literal["update", "overwrite", "upsert"] = "update",
) -> dict[str, Any]:
    """
    Generic wrapper.

    operation:
        - update
        - overwrite
        - upsert
    """

    operation = operation.lower()

    if operation == "update":
        return update_yaml_array_item(
            yaml_data=yaml_data,
            root_element=root_element,
            filters=filters,
            updates=data,
        )

    if operation == "overwrite":
        return overwrite_yaml_array_item(
            yaml_data=yaml_data,
            root_element=root_element,
            filters=filters,
            item=data,
        )

    if operation == "upsert":
        return upsert_yaml_array_item(
            yaml_data=yaml_data,
            root_element=root_element,
            filters=filters,
            item=data,
        )

    raise ValueError(
        f"Unsupported operation '{operation}'. "
        "Supported values: update, overwrite, upsert."
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





def render_template(
    template: str | None = None,
    template_file_path: str | None = None,
    variables: dict | None = None,
) -> str:

    if template_file_path:
        template = Path(template_file_path).read_text(
            encoding="utf-8"
        )

    if not template:
        raise ValueError(
            "template or template_file_path is required"
        )

    return Template(template).render(
        **(variables or {})
    )



def generate_openrouter_response(
    api_key: str,
    user_prompt: str,
    models: list[str],
    temperature: float = 0.2,
    timeout: int = 300,
) -> str:

    errors = []
    # Docs: https://openrouter.ai/openrouter/free

    for model in models:

        try:

            print(f"Trying model: {model}")

            system_prompt = """
            You are a trading strategy optimization engine.

            Return valid YAML only.
            Return only modified records.
            Never return markdown.
            Never return explanations.
            Never return code fences.
            Preserve YAML structure.
            """

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                    ],
                    "temperature": temperature,
                },
                timeout=timeout,
            )

            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"]

            print(f"Success using model: {model}")

            return content

        except requests.HTTPError as ex:

            status_code = (
                ex.response.status_code
                if ex.response is not None
                else "unknown"
            )

            error_message = (
                f"{model}: HTTP {status_code}: {str(ex)}"
            )

            print(error_message)

            errors.append(error_message)

            continue

        except requests.Timeout as ex:

            error_message = (
                f"{model}: Timeout: {str(ex)}"
            )

            print(error_message)

            errors.append(error_message)

            continue

        except Exception as ex:

            error_message = (
                f"{model}: {str(ex)}"
            )

            print(error_message)

            errors.append(error_message)

            continue

    raise RuntimeError(
        "All OpenRouter models failed.\n"
        + "\n".join(errors)
    )

def extract_yaml(text: str) -> dict:
    return yaml.safe_load(text)    

def main():
    # Profiles example
    profile_name = "asyafoek-stocks-long-swing-paper"
    filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/profiles.yaml"
    profiles_obj = from_yaml(Path(filename))
    paper_profile = retrieve_candidate_configuration(
        yaml_file_path=filename,
        root_element="Profiles",

        filters=[
            {
                "MatchPath": "Profile.Name",
                "MatchValues": [
                    profile_name,
                ]
            }
        ]
    )
    print(f"Config Profiles\n{to_yaml(paper_profile)}\n")

    # RiskReward example
    trend_regime="BEARISH"
    trend_volume="QUIET"
    filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/riskreward.yaml"
    riskreward_obj = from_yaml(Path(filename))
    paper_riskreward = retrieve_candidate_configuration(
        yaml_file_path=filename,
        root_element="RiskRewardNotations",
        filters=[
            {
                "MatchPath": "ProfileName",
                "MatchValues": [
                    profile_name,
                ],
            },
            {
                "MatchPath": "TrendRegime",
                "MatchValues": [
                    trend_regime,
                ],
            },
            {
                "MatchPath": "VolatilityRegime",
                "MatchValues": [
                    trend_volume,
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
    # print(f"Config RuleProviders\n{to_yaml(paper_ruleproviders)}\n")

    # Current Classification example
    current_class = "GoodLoss"
    filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/tradeclassifications.yaml"
    current_classification = retrieve_candidate_configuration(
        yaml_file_path=filename,
        root_element="TradeClassifications",
        filters=[
            {
                "MatchPath": "Classification",
                "MatchValues": [
                    current_class,
                ],
            }
        ],
    )
    # print(f"Current Classification\n{to_yaml(current_classification)}\n")

    # Target Classification example
    target_class = "GoodProfit"
    filename = "../../../../../corporate-it-intelligent-daytrading/src/resources/application-data/tradeclassifications.yaml"
    target_classification = retrieve_candidate_configuration(
        yaml_file_path=filename,
        root_element="TradeClassifications",
        filters=[
            {
                "MatchPath": "Classification",
                "MatchValues": [
                    target_class,
                ],
            }
        ],
    )
    # print(f"Target Classification\n{to_yaml(target_classification)}\n")

    filename= Path("../../../../../corporate-it-intelligent-daytrading/src/resources/templates/openrouter-tune.txt")
    failed_metrics = [
        "Signal_Match", 
        "Entry_Efficiency", 
        "Risk_Reward_Ratio", 
        "Win_Rate",
        "Risk_Control", 
    ]
    vars = {
        "TARGET_PROFILE_NAME": profile_name,
        "TREND_REGIME": trend_regime,
        "TREND_VOLUME": trend_volume,
        "CURRENT_CLASSIFICATION": current_class,
        "TARGET_CLASSIFICATION": target_class,
        "FAILED_METRICS": failed_metrics,
        "PROFILE_YAML": to_yaml(paper_profile),
        "RISKREWARD_YAML": to_yaml(paper_riskreward),
        "RULEPROVIDERS_YAML": to_yaml(paper_ruleproviders),
    }    
    request_prompt = render_template(template_file_path=filename, variables=vars)

    # print(request_prompt)

    api_key = os.getenv("OPENROUTER_APIKEY")
    # # models = ["deepseek/deepseek-r1:free", "deepseek/deepseek-r1-0528", "google/gemma-4-26b-a4b-it:free"]
    # # models = ["google/gemma-4-26b-a4b-it:free"]
    models = [
        "openrouter/free",
        # "minimax/minimax-m3:free",
        # "nvidia/nemotron-3-ultra-550b-a55b:free",
        # "liquid/lfm-2.5-embedding-350m:free",
        # "z-ai/glm-5.2:free",
    ]
    response_prompt = generate_openrouter_response(api_key, request_prompt, models)
    print("BEGIN RESPONSE")
    print(response_prompt)
    print("END RESPONSE")



    mergeResults = True
    if mergeResults:
        data = extract_yaml(response_prompt)
        profiles_adjusted = data.get("Profiles")
        riskrewards_adjusted = data.get("RiskRewardNotations")

        if profiles_adjusted:
            profiles_new = merge_yaml_array_item(
                yaml_data=profiles_obj,
                root_element="Profiles",
                operation="update",
                filters=[
                    {
                        "MatchPath": "Profile.Name",
                        "MatchValues": [
                            profile_name,
                        ]
                    }
                ],
                data=profiles_adjusted[0],
            )
            print(to_yaml(profiles_new)) 
            # print(to_yaml(profiles_adjusted)) 

        if riskrewards_adjusted:
            riskrewards_new = merge_yaml_array_item(
                yaml_data=riskreward_obj,
                root_element="RiskRewardNotations",
                operation="update",
                filters=[
                    {
                        "MatchPath": "ProfileName",
                        "MatchValues": [
                            profile_name,
                        ],
                    },
                    {
                        "MatchPath": "TrendRegime",
                        "MatchValues": [
                            trend_regime,
                        ],
                    },
                    {
                        "MatchPath": "VolatilityRegime",
                        "MatchValues": [
                            trend_volume,
                        ],
                    }
                ],
                data=riskrewards_adjusted[0],
            )
            print(to_yaml(riskrewards_new)) 
            # print(to_yaml(riskrewards_adjusted)) 

if __name__ == "__main__":
    main()

