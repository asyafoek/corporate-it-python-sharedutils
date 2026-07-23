from abc import ABC
from abc import abstractmethod

import pandas as pd


class SignalProvider(ABC):

    @abstractmethod
    def evaluate(
        self,
        profile: dict,
        watchlist_entry: dict,
        market_data: pd.DataFrame,
        open_orders: pd.DataFrame,
        reward_risk_ratio: float
    ) -> list:
        """
        Evaluate market conditions and return
        zero or more trading signals.
        """
        pass