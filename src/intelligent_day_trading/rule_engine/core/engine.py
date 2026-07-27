from .engine_configs import (
    ENGINE_CONFIGS
)

from .provider_loader import (
    load_provider
)


class RuleEngine:

    def __init__(
        self,
        engine_version
    ):

        self.providers = []

        for provider_name, version in (
            ENGINE_CONFIGS[engine_version]
        ):

            self.providers.append(

                load_provider(
                    provider_name,
                    version
                )

            )