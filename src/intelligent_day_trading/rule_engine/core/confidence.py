from dataclasses import dataclass


@dataclass
class ConfidenceResult:
    confidence: float
    validations: list[dict]


class ConfidenceCalculator:

    @staticmethod
    def calculate(
        conditions: dict[str, bool],
        weights: dict[str, float]
    ) -> ConfidenceResult:

        confidence = 0.0
        validations = []

        for validation_name, passed in conditions.items():

            weight = weights.get(
                validation_name,
                0.0
            )

            contribution = (
                weight
                if passed
                else 0.0
            )

            confidence += contribution

            validations.append(
                {
                    "validation": validation_name,
                    "passed": passed,
                    "weight": weight,
                    "contribution": contribution
                }
            )

        confidence = round(
            min(confidence, 1.0),
            4
        )

        return ConfidenceResult(
            confidence=confidence,
            validations=validations
        )