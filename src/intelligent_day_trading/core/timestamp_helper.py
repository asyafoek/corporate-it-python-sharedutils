import pandas as pd


class TimestampHelper:

    SUPPORTED_PRECISIONS = {
        "ms",
        "ns"
    }

    @staticmethod
    def detect_precision(
        ts: pd.Timestamp
    ) -> str:

        if ts.value % 1_000_000 == 0:
            return "ms"

        return "ns"

    @classmethod
    def market_timestamp(
        cls,
        ts: pd.Timestamp,
        precision: str
    ) -> int:

        if precision not in cls.SUPPORTED_PRECISIONS:

            raise ValueError(
                f"Unsupported precision: "
                f"{precision}"
            )

        if ts.tzinfo is None:
            ts = ts.tz_localize(
                "UTC"
            )
        else:
            ts = ts.tz_convert(
                "UTC"
            )

        if precision == "ms":
            return (
                ts.value
                // 1_000_000
            )

        return ts.value

    @classmethod
    def signal_timestamp(
        cls,
        precision: str
    ) -> int:

        if precision not in cls.SUPPORTED_PRECISIONS:

            raise ValueError(
                f"Unsupported precision: "
                f"{precision}"
            )

        now = pd.Timestamp.utcnow()

        if precision == "ms":
            return (
                now.value
                // 1_000_000
            )

        return now.value