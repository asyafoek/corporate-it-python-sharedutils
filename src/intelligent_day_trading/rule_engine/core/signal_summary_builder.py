class SignalSummaryBuilder:

    @staticmethod
    def build(
        trading_signals
    ):

        summary = {

            "long": {
                "buy": 0,
                "wait": 0,
                "sell": 0
            },

            "short": {
                "buy": 0,
                "wait": 0,
                "sell": 0
            }
        }

        for signal in trading_signals:

            summary[
                signal["side"]
            ][
                signal["signal"]
            ] += 1

        for side in [
            "long",
            "short"
        ]:

            total = sum(
                summary[
                    side
                ].values()
            )

            if total == 0:
                continue

            summary[
                side
            ] = {

                "buy_percentage":
                    round(
                        summary[
                            side
                        ][
                            "buy"
                        ] / total * 100,
                        2
                    ),

                "wait_percentage":
                    round(
                        summary[
                            side
                        ][
                            "wait"
                        ] / total * 100,
                        2
                    ),

                "sell_percentage":
                    round(
                        summary[
                            side
                        ][
                            "sell"
                        ] / total * 100,
                        2
                    )
            }

        return summary