from __future__ import annotations

from copy import deepcopy
from typing import Any
from pathlib import Path
from typing import Any
from jinja2 import Template
import requests
import yaml
from copy import deepcopy
from typing import Any

def to_yaml(data: dict) -> str:
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def _get_by_path(obj: dict[str, Any], path: str) -> Any:
    current = obj

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

        if current is None:
            return None

    return current


def _set_by_path(obj: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = obj

    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}

        current = current[part]

    current[parts[-1]] = value


def _find_matching_item(
    items: list[dict[str, Any]],
    match_items: list[tuple[str, Any]],
) -> tuple[int | None, dict[str, Any] | None]:
    """
    Find first item where ALL match_items match.

    Example:
        [
            ("id", "trend_bull"),
            ("ruleEngineVersion", 2),
        ]
    """

    for index, item in enumerate(items):
        if all(
            _get_by_path(item, path) == value
            for path, value in match_items
        ):
            return index, item

    return None, None


def update_yaml_array_item(
    yaml_data: dict[str, Any],
    root_path: str,
    match_items: list[tuple[str, Any]],
    updates: dict[str, Any],
) -> dict[str, Any]:
    """
    Update fields on an existing item.

    Raises:
        ValueError if item not found.
    """

    result = deepcopy(yaml_data)

    items = result[root_path]

    if not isinstance(items, list):
        raise ValueError(f"{root_path} is not a list")

    _, item = _find_matching_item(
        items=items,
        match_items=match_items,
    )

    if item is None:
        raise ValueError("No matching item found")

    for path, value in updates.items():
        _set_by_path(item, path, value)

    return result


def overwrite_yaml_array_item(
    yaml_data: dict[str, Any],
    root_path: str,
    match_items: list[tuple[str, Any]],
    item: dict[str, Any],
) -> dict[str, Any]:
    """
    Completely replace an existing item.

    Raises:
        ValueError if item not found.
    """

    result = deepcopy(yaml_data)

    items = result[root_path]

    if not isinstance(items, list):
        raise ValueError(f"{root_path} is not a list")

    index, _ = _find_matching_item(
        items=items,
        match_items=match_items,
    )

    if index is None:
        raise ValueError("No matching item found")

    items[index] = deepcopy(item)

    return result


def upsert_yaml_array_item(
    yaml_data: dict[str, Any],
    root_path: str,
    match_items: list[tuple[str, Any]],
    item: dict[str, Any],
) -> dict[str, Any]:
    """
    Update existing item if found.
    Insert new item if not found.
    """

    result = deepcopy(yaml_data)

    items = result[root_path]

    if not isinstance(items, list):
        raise ValueError(f"{root_path} is not a list")

    _, existing_item = _find_matching_item(
        items=items,
        match_items=match_items,
    )

    if existing_item is not None:

        for path, value in item.items():
            _set_by_path(existing_item, path, value)

    else:
        items.append(deepcopy(item))

    return result


def merge_yaml_array_item(
    yaml_data: dict[str, Any],
    root_path: str,
    operation: str,
    match_items: list[tuple[str, Any]],
    data: dict[str, Any],
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
            root_path=root_path,
            match_items=match_items,
            updates=data,
        )

    if operation == "overwrite":
        return overwrite_yaml_array_item(
            yaml_data=yaml_data,
            root_path=root_path,
            match_items=match_items,
            item=data,
        )

    if operation == "upsert":
        return upsert_yaml_array_item(
            yaml_data=yaml_data,
            root_path=root_path,
            match_items=match_items,
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
    prompt: str,
    models: list[str],
    temperature: float = 0.2,
    timeout: int = 300,
) -> str:

    errors = []

    for model in models:

        try:

            print(f"Trying model: {model}")

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
                            "role": "user",
                            "content": prompt,
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
    print(f"Config RuleProviders\n{to_yaml(paper_ruleproviders)}\n")

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
    print(f"Current Classification\n{to_yaml(current_classification)}\n")

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
    print(f"Target Classification\n{to_yaml(target_classification)}\n")

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

    # api_key = ""
    # # models = ["deepseek/deepseek-r1:free", "deepseek/deepseek-r1-0528", "google/gemma-4-26b-a4b-it:free"]
    # # models = ["google/gemma-4-26b-a4b-it:free"]
    # models = [
    #         "openrouter/free",
    #         "google/gemma-4-26b-it:free",
    #         "openai/gpt-oss-120b:free",
    #         "openai/gpt-oss-20b:free",
    #         ]
    # response_prompt = generate_openrouter_response(api_key, request_prompt, models)
    # print(response_prompt)



    # ------------------------------------------------------------------
    # EXAMPLE
    # ------------------------------------------------------------------

    config = {
        "riskRewardProfiles": [
            {
                "id": "trend_bull",
                "ruleEngineVersion": 2,
                "enabled": True,
            },
            {
                "id": "trend_bear",
                "ruleEngineVersion": 2,
                "enabled": True,
            },
        ]
    }

    result = merge_yaml_array_item(
        yaml_data=config,
        root_path="riskRewardProfiles",
        operation="update",
        match_items=[
            ("id", "trend_bull"),
            ("ruleEngineVersion", 2),
        ],
        data={
            "enabled": False,
        },
    )

    print(result) 

    # data = extract_yaml(response_prompt)
    # profiles_adjusted = data["Profiles"]
    # risk_rewards_adjusted = data["RiskRewardNotations"]
    # TODO Do the merge logic

if __name__ == "__main__":
    main()

