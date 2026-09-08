from __future__ import annotations

from datetime import datetime, timezone
from pprint import pprint
from uuid import uuid4

import json
from sqlalchemy import text

class DataFlow:

    DEFAULT_CONTEXT_TABLE = "trade_dataflow_context"
    DEFAULT_STEP_TABLE = "trade_dataflow_step"

    def __init__(
        self,
        context: dict | None = None,
        external_reference_id: str | None = None,
        lookup_key: str | None = None,
        context_table_name: str | None = None,
        step_table_name: str | None = None,
    ):

        self.external_reference_id = (
            external_reference_id or str(uuid4())
        )

        self.lookup_key = lookup_key

        self.context_table_name = (
            context_table_name
            or self.DEFAULT_CONTEXT_TABLE
        )

        self.step_table_name = (
            step_table_name
            or self.DEFAULT_STEP_TABLE
        )

        self.status = "NEW"

        self.start_timestamp = datetime.now(timezone.utc)
        self.finish_timestamp = None

        self.context = context or {}

        self.steps = []

    def set_context(self, context: dict | None) -> None:
        self.context = context or {}

    def get_context(self) -> dict:
        return self.context

    @property
    def lookup_key(self) -> str | None:
        return self._lookup_key

    @lookup_key.setter
    def lookup_key(self, value: str | None):

        if value is None:
            self._lookup_key = None
            return

        self._lookup_key = str(value).strip()

    def add_step(
        self,
        step_name: str,
        payload: dict,
        timestamp: datetime | None = None,
    ):

        event_timestamp = (
            timestamp
            if timestamp is not None
            else datetime.now(timezone.utc)
        )

        self.steps.append(
            {
                "step_name": step_name,
                "event_timestamp": event_timestamp,
                "payload": payload,
            }
        )

        if self.status not in ("SUCCESS", "FAILED"):
            self.status = "IN_PROGRESS"

    @property
    def first_step(self):

        if not self.steps:
            return None

        return self.steps[0]

    @property
    def last_step(self):

        return self.steps[-1] if self.steps else None

    def success(self):

        self.status = "SUCCESS"
        self.finish_timestamp = datetime.now(timezone.utc)

    def failed(self):

        self.status = "FAILED"
        self.finish_timestamp = datetime.now(timezone.utc)

    def pause(self):

        self.status = "PAUSED"

    def resume(self):

        self.status = "IN_PROGRESS"


    @property
    def is_finished(self):

        return self.finish_timestamp is not None

    @property
    def total_steps(self):

        return len(self.steps)

    def print(self):

        print("\n" + "=" * 120)
        print("DATAFLOW")
        print("=" * 120)

        print(f"external_reference_id : {self.external_reference_id}")
        print(f"lookup_key : {self.lookup_key}")
        print(f"status                : {self.status}")
        print(f"start_timestamp        : {self.start_timestamp}")
        print(f"finish_timestamp       : {self.finish_timestamp}")

        print("\nCONTEXT")
        print("-" * 120)
        pprint(self.context)

        print("\nSTEPS")
        print("-" * 120)

        for i, step in enumerate(self.steps, start=1):

            print(f"\nSTEP {i}")
            print(
                f"{step['event_timestamp']} "
                f"- {step['step_name']}"
            )

            pprint(step["payload"])

    def to_dict(self):

        return {
            "external_reference_id": self.external_reference_id,
            "lookup_key": self.lookup_key,
            "status": self.status,
            "start_timestamp": self.start_timestamp.isoformat(),
            "finish_timestamp": (
                self.finish_timestamp.isoformat()
                if self.finish_timestamp
                else None
            ),
            "context": self.context,
            "steps": [
                {
                    "step_name": step["step_name"],
                    "event_timestamp": (
                        step["event_timestamp"].isoformat()
                    ),
                    "payload": step["payload"],
                }
                for step in self.steps
            ],
        }



    def save(self, engine):

        with engine.begin() as conn:

            # context record

            conn.execute(
                text(
                    f"""
                    INSERT INTO {self.context_table_name}
                    (
                        external_reference_id,
                        lookup_key,
                        status,
                        start_timestamp,
                        finish_timestamp,
                        context_json
                    )
                    VALUES
                    (
                        :external_reference_id,
                        :lookup_key,
                        :status,
                        :start_timestamp,
                        :finish_timestamp,
                        CAST(:context_json AS JSONB)
                    )
                    ON CONFLICT (external_reference_id)
                    DO UPDATE
                    SET
                        lookup_key = EXCLUDED.lookup_key,
                        status = EXCLUDED.status,
                        finish_timestamp = EXCLUDED.finish_timestamp,
                        context_json = EXCLUDED.context_json
                    """
                ),
                {
                    "external_reference_id": self.external_reference_id,
                    "lookup_key": self.lookup_key,
                    "status": self.status,
                    "start_timestamp": self.start_timestamp,
                    "finish_timestamp": self.finish_timestamp,
                    "context_json": json.dumps(self.context),
                },
            )

            # alle steps opnieuw schrijven

            conn.execute(
                text(
                    f"""
                    DELETE
                    FROM {self.step_table_name}
                    WHERE external_reference_id =
                        :external_reference_id
                    """
                ),
                {
                    "external_reference_id": self.external_reference_id,
                },
            )

            for step in self.steps:

                conn.execute(
                    text(
                        f"""
                        INSERT INTO {self.step_table_name}
                        (
                            external_reference_id,
                            step_name,
                            event_timestamp,
                            payload_json
                        )
                        VALUES
                        (
                            :external_reference_id,
                            :step_name,
                            :event_timestamp,
                            CAST(:payload_json AS JSONB)
                        )
                        """
                    ),
                    {
                        "external_reference_id":
                            self.external_reference_id,
                        "step_name":
                            step["step_name"],
                        "event_timestamp":
                            step["event_timestamp"],
                        "payload_json":
                            json.dumps(step["payload"]),
                    },
                )

    @staticmethod
    def load(
        engine,
        external_reference_id: str | None = None,
        lookup_key: str | None = None,
        status: str | None = None,
        context_table_name: str = "trade_dataflow_context",
        step_table_name: str = "trade_dataflow_step",
    ):

        if external_reference_id is not None:

            sql = f"""
            SELECT *
            FROM {context_table_name}
            WHERE external_reference_id = :external_reference_id
            LIMIT 1
            """

            params = {
                "external_reference_id": external_reference_id
            }

        elif lookup_key is not None:

            sql = f"""
            SELECT *
            FROM {context_table_name}
            WHERE lookup_key = :lookup_key
            """

            params = {
                "lookup_key": lookup_key
            }

            if status is not None:

                sql += """
                AND status = :status
                """

                params["status"] = status

            sql += """
            ORDER BY start_timestamp DESC
            LIMIT 1
            """

        else:

            raise ValueError(
                "external_reference_id or lookup_key required"
            )

        with engine.connect() as conn:

            # context laden

            row = conn.execute(
                text(sql),
                params,
            ).mappings().first()

            if row is None:
                return None

            flow = DataFlow(
                context=row["context_json"],
                external_reference_id=row["external_reference_id"],
                lookup_key=row["lookup_key"],
                context_table_name=context_table_name,
                step_table_name=step_table_name,
            )

            # status herstellen

            flow.status = row["status"]
            flow.start_timestamp = row["start_timestamp"]
            flow.finish_timestamp = row["finish_timestamp"]

            # steps laden

            step_rows = conn.execute(
                text(
                    f"""
                    SELECT
                        step_name,
                        event_timestamp,
                        payload_json
                    FROM {step_table_name}
                    WHERE external_reference_id =
                        :external_reference_id
                    ORDER BY event_timestamp
                    """
                ),
                {
                    "external_reference_id":
                        flow.external_reference_id
                },
            ).mappings().all()

            for step_row in step_rows:

                flow.steps.append(
                    {
                        "step_name":
                            step_row["step_name"],

                        "event_timestamp":
                            step_row["event_timestamp"],

                        "payload":
                            step_row["payload_json"],
                    }
                )


            return flow

def main():

    flow = DataFlow(
        context={
            "broker_id": "Alpaca",
            "market": "NASDAQ",
            "account_id": "1",
            "trading_mode": "Paper",
            "symbol": "AAPL",
            "strategy": "Swing",
            "timeframe": "15m",
            "regime": "BULLISH_VOLATILE",
        }
    )

    flow = DataFlow()
    flow.set_context(
                context={
            "broker_id": "Alpaca",
            "market": "NASDAQ",
            "account_id": "1",
            "trading_mode": "Paper",
            "symbol": "AAPL",
            "strategy": "Swing",
            "timeframe": "15m",
            "regime": "BULLISH_VOLATILE",
        }
    )

    flow.add_step(
        "bar_received",
        {
            "ticker": "NVDA",
            "t": "2026-08-25T10:15:00Z",
            
            "open": 181.10,
            "high": 181.35,
            "low": 180.95,
            "close": 181.25,
        
            "volume": 1250000,
            "vwap": 181.18,
        
            "market": "Stocks",
            "trading_mode": "Live"
        },
    )

    flow.add_step(
        "opportunity_detected",
        {
            "opportunity_detected": True,
            "added_in_cache": "20260826T07:32:42+02:00"
        },
    )


    flow.add_step(
        "bars_enriched",
        {
            "signal_window": [
                {"o": 181.10, "h": 181.35,  "l": 180.95, "c": 181.25, "v": 1250000, "vw": 181.18, "t": 12345789012345, "sma20": 180.91, "ema20": 181.02, "rsi14": 63.42, "macd": 1.23, "macd_signal": 1.1}
            ]
        },
    )

    flow.add_step(
        "signal_evaluated",
        {
            "action": "Buy",
            "percentage": 75,
            "provider_count_configured": 12,
            "provider_count_evaluated": 8,
            "providers_evaluated": ["trend","reversal"],
            "providers_not_evaluated": ["news"]
        },
    )

    flow.add_step(
        "risk_assessed",
        {
            "decision": "Accepted",
            "reason": None,
            "position_sizing": "KellyCriterion",
            "risk_modal": "ATR",
            "risk_reward_notation": "1:1.5",
            "risk_reward_ratio": 1.5,
            "minimum_holding_periode": "20260826T08:20:16+02:00",
            "maximum_holding_periode": "20260826T09:20:16+02:00"
        },
    )

    flow.add_step(
        "trade_open",
        {
            "secrets": "alpaca-paper-credentials",
            "client_order_id": "550e8400-e29b-41d4-a716-446655440000",
            "order_id": "XSFWR##444444",
            "broker": "Alpaca",
            "action": "Buy",
            "ticker": "NVDA",
            "requested_size": 6,
            "requested_price": 181.25,
            "stop_loss": 180.95,
            "take_profit": 181.25,
            "spread": 0.04,
            "status": "Accepted",
            "expiration_timestamp": "20260826T21:20:16+02:00"
        },
    )

    flow.add_step(
        "position_open",
        {
            "secrets": "alpaca-paper-credentials",
            "broker": "Alpaca",
            "action": "Buy",
            "ticker": "NVDA",
            "fill_size": 6,
            "fill_price": 181.25,
            "fees": 0.20,
            "timestamp": "20260826T08:03:54.321+02:00"
        },
    )

    flow.add_step(
        "trade_close",
        {
            "secrets": "alpaca-paper-credentials",
            "client_order_id": "550e8400-e29b-41d4-a716-446655440000",
            "order_id": "XSFWR##444444",
            "broker": "Alpaca",
            "action": "Sell",
            "ticker": "NVDA",
            "requested_size": 6,
            "requested_price": 181.25,
            "status": "Accepted",
            "expiration_timestamp": "20260826T21:20:16+02:00"
        },
    )

    flow.add_step(
        "position_close",
        {
            "secrets": "alpaca-paper-credentials",
            "broker": "Alpaca",
            "action": "Sell",
            "ticker": "NVDA",
            "exit_size": 6,
            "exit_price": 181.25,
            "fees": 0.20,
            "timestamp": "20260826T08:03:54.321+02:00"
        },
    )

    flow.add_step(
        "trade_result",
        {
            "gross_profit": 31.50,
            "net_profit": 29.00,
            "entry_price": 181.25,
            "exit_price": 230.25,
            "entry_size": 6,
            "exit_size": 6,
            "return_pct": 2.65,
            "exit_reason": "Exit Signal",
            "holding_minutes": 3.6,
            "realized_risk_reward_ratio": 1.5,
            "winner": True
        },
    )

    flow.success()

    # flow.print()

    print("\nAS DICT")
    pprint(flow.to_dict())

    print("\nFirst Step")
    print(flow.first_step)

    print("\nLast Step")
    print(flow.last_step)

if __name__ == "__main__":
    main()