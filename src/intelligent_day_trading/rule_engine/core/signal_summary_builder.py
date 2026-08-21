class SignalSummaryBuilder:

    @staticmethod
    def build(
        trading_signals
    ):

        summary = {

            "long": {
                "buy": 0,
                "wait": 0,
                "sell": 0,
                "provider_count": 0,
                "providers_with_signal": 0,
                "providers_without_signal": 0                
            },

            "short": {
                "buy": 0,
                "wait": 0,
                "sell": 0,
                "provider_count": 0,
                "providers_with_signal": 0,
                "providers_without_signal": 0                
            }
        }

        # for signal in trading_signals:

        #     summary[
        #         signal["side"]
        #     ][
        #         signal["signal"]
        #     ] += signal[
        #         "confidence_percentage"
        #     ]

        for signal in trading_signals:

            side = signal["side"].lower()

            summary[side]["provider_count"] += 1

            # if signal["signal"] is None:
            #     continue

            if signal["signal"] is None:
                summary[side][
                    "providers_without_signal"
                ] += 1
                continue

            summary[side][
                "providers_with_signal"
            ] += 1

            summary[
                side
            ][
                signal["signal"].lower()
            ] += signal[
                "confidence_percentage"
            ]

        for side in [
            "long",
            "short"
        ]:

            # total = sum(
            #     summary[
            #         side
            #     ].values()
            # )

            total = (
                summary[side]["buy"]
                + summary[side]["wait"]
                + summary[side]["sell"]
            )

            # if total == 0:
            #     continue

            if total == 0:
                # summary[side] = {
                #     "buy_percentage": 0,
                #     "wait_percentage": 0,
                #     "sell_percentage": 0,

                #     "provider_count":
                #         summary[side]["provider_count"]
                # }

                summary[side] = {
                    "buy_percentage": 0,
                    "wait_percentage": 0,
                    "sell_percentage": 0,

                    "provider_count":
                        summary[side]["provider_count"],

                    "providers_with_signal":
                        summary[side]["providers_with_signal"],

                    "providers_without_signal":
                        summary[side]["providers_without_signal"]
                }

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
                    ),

                "provider_count":
                    summary[side]["provider_count"],

                "providers_with_signal":
                    summary[side]["providers_with_signal"],

                "providers_without_signal":
                    summary[side]["providers_without_signal"]


                }


        return summary