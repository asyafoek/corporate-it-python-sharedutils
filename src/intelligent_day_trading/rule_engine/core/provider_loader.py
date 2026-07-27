import importlib


def load_provider(
    provider_name,
    provider_version
):

    module = importlib.import_module(

        f"intelligent_day_trading."
        f"rule_engine."
        f"providers."
        f"{provider_name}."
        f"v{provider_version}"

    )

    provider = module.Provider()

    provider.provider_name = (
        provider_name
    )

    provider.provider_version = (
        provider_version
    )

    return provider