from __future__ import annotations

from datetime import datetime, timezone
from datetime import timedelta
from pprint import pprint
from uuid import uuid4

import json
from sqlalchemy import text
import os

class DataFlow:

    DEFAULT_SCHEMA_NAME = "raw"
    DEFAULT_CONTEXT_TABLE = "idts_all_market_dataflow_context_persisted_1"
    DEFAULT_STEP_TABLE = "idts_all_market_dataflow_step_persisted_1"

    def __init__(
        self,
        context: dict | None = None,
        external_reference_id: str | None = None,
        lookup_key: str | None = None,
        context_table_name: str | None = None,
        schema_name: str | None = None,
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


        self.schema_name = (
            schema_name
            or self.DEFAULT_SCHEMA_NAME
        )

        self.new()

        self.start_timestamp = datetime.now(timezone.utc)
        self.finish_timestamp = None
        self._retention = None

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

        # if self.status not in ("SUCCESS", "FAILED"):
        #     self.status = "IN_PROGRESS"

    @property
    def first_step(self):

        if not self.steps:
            return None

        return self.steps[0]

    @property
    def last_step(self):

        return self.steps[-1] if self.steps else None

    def new(self):

        self.status = "NEW"

    def open(self):

        self.status = "OPEN"

    def closed(self):

        self.status = "CLOSED"
        self.finish_timestamp = datetime.now(timezone.utc)

    def aborted(self):

        self.status = "ABORTED"
        self.finish_timestamp = datetime.now(timezone.utc)

    def completed(self):

        self.status = "COMPLETED"
        self.finish_timestamp = datetime.now(timezone.utc)

    def success(self):

        self.status = "SUCCESS"
        self.finish_timestamp = datetime.now(timezone.utc)

    def failed(self):

        self.status = "FAILED"
        self.finish_timestamp = datetime.now(timezone.utc)

    def pause(self):

        self.status = "PAUSED"
        self.finish_timestamp = None

    def inProgress(self):

        self.status = "IN_PROGRESS"
        self.finish_timestamp = None

    def resume(self):

        self.status = "IN_PROGRESS"
        self.finish_timestamp = None


    @property
    def is_finished(self):

        return self.finish_timestamp is not None

    def _retention_to_timedelta(
        self,
        retention: str,
    ) -> timedelta:

        retention = retention.strip().lower()

        if retention.endswith("ms"):
            return timedelta(
                milliseconds=int(retention[:-2])
            )

        if retention.endswith("s"):
            return timedelta(
                seconds=int(retention[:-1])
            )

        if retention.endswith("m"):
            return timedelta(
                minutes=int(retention[:-1])
            )

        if retention.endswith("h"):
            return timedelta(
                hours=int(retention[:-1])
            )

        if retention.endswith("d"):
            return timedelta(
                days=int(retention[:-1])
            )

        raise ValueError(
            f"Unsupported retention value: {retention}"
        )

    @property
    def retention(self) -> str | None:
        return self._retention

    @retention.setter
    def retention(
        self,
        value: str | None,
    ):

        if value is None:
            self._retention = None
            return

        self._retention = str(value).strip()

    @property
    def expiration_timestamp(
        self,
    ) -> datetime | None:

        if self.retention is None:
            return None

        return (
            self.start_timestamp
            + self._retention_to_timedelta(
                self.retention
            )
        )

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
            "retention": self.retention,
            "expiration_timestamp": (
                self.expiration_timestamp.isoformat()
                if self.expiration_timestamp
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

    @classmethod
    def from_dict(cls, data: dict) -> "DataFlow":

        flow = cls(
            context=data.get("context"),
            external_reference_id=data.get(
                "external_reference_id"
            ),
            lookup_key=data.get("lookup_key"),
        )

        flow.status = data.get("status", "NEW")

        flow.start_timestamp = datetime.fromisoformat(
            data["start_timestamp"]
        )

        flow.finish_timestamp = (
            datetime.fromisoformat(data["finish_timestamp"])
            if data.get("finish_timestamp")
            else None
        )

        flow.retention = data.get("retention")

        flow.steps = [
            {
                "step_name": step["step_name"],
                "event_timestamp": datetime.fromisoformat(
                    step["event_timestamp"]
                ),
                "payload": step["payload"],
            }
            for step in data.get("steps", [])
        ]

        return flow


    def to_json(self) -> str:
        return json.dumps( self.to_dict(), indent=4)


    @classmethod
    def from_json(
        cls,
        text: str,
    ) -> "DataFlow":
        return cls.from_dict(json.loads(text))


    def to_backingstore(self, engine):

        with engine.begin() as conn:

            # =====================================================================
            # CREATE TABLES IF THEY DO NOT EXIST
            # =====================================================================

            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.schema_name}.{self.context_table_name}
                    (
                        external_reference_id VARCHAR(255) PRIMARY KEY,
                        lookup_key VARCHAR(255),
                        status VARCHAR(50) NOT NULL,
                        start_timestamp TIMESTAMPTZ NOT NULL,
                        finish_timestamp TIMESTAMPTZ,
                        retention VARCHAR(100),
                        expiration_timestamp TIMESTAMPTZ,
                        context_json JSONB NOT NULL
                    )
                    """
                )
            )

            print("table")

            conn.execute(
                text(
                    f"""
                    CREATE INDEX IF NOT EXISTS
                        idx_{self.context_table_name}_lookup_key
                    ON {self.schema_name}.{self.context_table_name}
                    (
                        lookup_key
                    )
                    """
                )
            )

            print("index")

            conn.execute(
                text(
                    f"""
                    CREATE INDEX IF NOT EXISTS
                        idx_{self.context_table_name}_status
                    ON {self.schema_name}.{self.context_table_name}
                    (
                        status
                    )
                    """
                )
            )

            print("table")

            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.schema_name}.{self.step_table_name}
                    (
                        id BIGSERIAL PRIMARY KEY,
                        external_reference_id VARCHAR(255) NOT NULL,
                        step_name VARCHAR(255) NOT NULL,
                        event_timestamp TIMESTAMPTZ NOT NULL,
                        payload_json JSONB NOT NULL,

                        CONSTRAINT fk_{self.step_table_name}
                        FOREIGN KEY (external_reference_id)
                        REFERENCES {self.schema_name}.{self.context_table_name}
                        (
                            external_reference_id
                        )
                        ON DELETE CASCADE
                    )
                    """
                )
            )

            print("index")

            conn.execute(
                text(
                    f"""
                    CREATE INDEX IF NOT EXISTS
                        idx_{self.step_table_name}_external_reference_id
                    ON {self.schema_name}.{self.step_table_name}
                    (
                        external_reference_id
                    )
                    """
                )
            )

            conn.execute(
                text(
                    f"""
                    CREATE INDEX IF NOT EXISTS
                        idx_{self.step_table_name}_event_timestamp
                    ON {self.schema_name}.{self.step_table_name}
                    (
                        event_timestamp
                    )
                    """
                )
            )

            # =====================================================================
            # CONTEXT RECORD
            # =====================================================================

            conn.execute(
                text(
                    f"""
                    INSERT INTO {self.schema_name}.{self.context_table_name}
                    (
                        external_reference_id,
                        lookup_key,
                        status,
                        start_timestamp,
                        finish_timestamp,
                        retention,
                        expiration_timestamp,
                        context_json
                    )
                    VALUES
                    (
                        :external_reference_id,
                        :lookup_key,
                        :status,
                        :start_timestamp,
                        :finish_timestamp,
                        :retention,
                        :expiration_timestamp,
                        CAST(:context_json AS JSONB)
                    )
                    ON CONFLICT (external_reference_id)
                    DO UPDATE
                    SET
                        lookup_key = EXCLUDED.lookup_key,
                        status = EXCLUDED.status,
                        finish_timestamp = EXCLUDED.finish_timestamp,
                        retention = EXCLUDED.retention,
                        expiration_timestamp = EXCLUDED.expiration_timestamp,
                        context_json = EXCLUDED.context_json
                    """
                ),
                {
                    "external_reference_id":
                        self.external_reference_id,
                    "lookup_key":
                        self.lookup_key,
                    "status":
                        self.status,
                    "start_timestamp":
                        self.start_timestamp,
                    "finish_timestamp":
                        self.finish_timestamp,
                    "retention":
                        self.retention,
                    "expiration_timestamp":
                        self.expiration_timestamp,
                    "context_json":
                        json.dumps(self.context),
                },
            )

            # alle steps opnieuw schrijven

            conn.execute(
                text(
                    f"""
                    DELETE
                    FROM {self.schema_name}.{self.step_table_name}
                    WHERE external_reference_id =
                        :external_reference_id
                    """
                ),
                {
                    "external_reference_id":
                        self.external_reference_id,
                },
            )

            for step in self.steps:

                conn.execute(
                    text(
                        f"""
                        INSERT INTO {self.schema_name}.{self.step_table_name}
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

        print("inserted or updated")

    @classmethod
    def from_backingstore(
        cls,
        engine,
        external_reference_id: str | None = None,
        lookup_key: str | None = None,
        status: str | None = None,
        schema_name: str = DEFAULT_SCHEMA_NAME,
        context_table_name: str = DEFAULT_CONTEXT_TABLE,
        step_table_name: str = DEFAULT_STEP_TABLE,
    ):

        if external_reference_id is not None:

            sql = f"""
            SELECT *
            FROM {schema_name}.{context_table_name}
            WHERE external_reference_id = :external_reference_id
            LIMIT 1
            """

            params = {
                "external_reference_id":
                    external_reference_id
            }

        elif lookup_key is not None:

            sql = f"""
            SELECT *
            FROM {schema_name}.{context_table_name}
            WHERE lookup_key LIKE :lookup_key
            """

            params = {
                "lookup_key":
                    f"{lookup_key}%"
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

            row = conn.execute(
                text(sql),
                params,
            ).mappings().first()

            if row is None:
                return None

            flow = cls(
                context=row["context_json"],
                external_reference_id=row["external_reference_id"],
                lookup_key=row["lookup_key"],
                context_table_name=context_table_name,
                step_table_name=step_table_name,
                schema_name=schema_name,
            )

            flow.status = row["status"]
            flow.start_timestamp = row["start_timestamp"]
            flow.finish_timestamp = row["finish_timestamp"]
            flow.retention = row["retention"]

            step_rows = conn.execute(
                text(
                    f"""
                    SELECT
                        step_name,
                        event_timestamp,
                        payload_json
                    FROM {schema_name}.{step_table_name}
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
    # market_data = "Massive"
    # broker_name = "Alpaca"
    # market = "Stocks"
    # symbol = "AAPL"

    market_data = "Massive"
    broker_name = "OKX"
    market = "Crypto"
    symbol = "X:BTC-USD"

    lookup_key = f"{market}|{market_data}|{symbol}|Long"
    search_key = f"{market}|{market_data}|{symbol}"
    # status = "IN_PROGRESS"
    status = "OPEN"

    flow = DataFlow(
        context={
            "broker_id": f"{broker_name}",
            "market": f"{market}",
            "account_id": "1",
            "trading_mode": "Paper",
            "symbol": f"{symbol}",
            "strategy": "Swing",
            "timeframe": "15m",
            "regime": "BULLISH_VOLATILE",
        }
    )

    flow = DataFlow()
    flow.set_context(
                context={
            "broker_id": f"{broker_name}",
            "market": f"{market}",
            "account_id": "1",
            "trading_mode": "Paper",
            "symbol": f"{symbol}",
            "strategy": "Swing",
            "timeframe": "15m",
            "regime": "BULLISH_VOLATILE",
        }
    )

    flow.add_step(
        "bar_received",
        {
            "ticker": f"{symbol}",
            "t": "2026-08-25T10:15:00Z",
            
            "open": 181.10,
            "high": 181.35,
            "low": 180.95,
            "close": 181.25,
        
            "volume": 1250000,
            "vwap": 181.18,
        
            "market": f"{market}",
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
            "broker": f"{broker_name}",
            "action": "Buy",
            "ticker": f"{symbol}",
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
            "secrets": f"{broker_name.lower()}-paper-credentials",
            "broker": f"{broker_name}",
            "action": "Buy",
            "ticker": f"{symbol}",
            "fill_size": 6,
            "fill_price": 181.25,
            "fees": 0.20,
            "timestamp": "20260826T08:03:54.321+02:00"
        },
    )

    flow.add_step(
        "trade_close",
        {
            "secrets": f"{broker_name.lower()}-paper-credentials",
            "client_order_id": "550e8400-e29b-41d4-a716-446655440000",
            "order_id": "XSFWR##444444",
            "broker": f"{broker_name}",
            "action": "Sell",
            "ticker": f"{symbol}",
            "requested_size": 6,
            "requested_price": 181.25,
            "status": "Accepted",
            "expiration_timestamp": "20260826T21:20:16+02:00"
        },
    )

    flow.add_step(
        "position_close",
        {
            "secrets": f"{broker_name.lower()}-paper-credentials",
            "broker": f"{broker_name}",
            "action": "Sell",
            "ticker": f"{symbol}",
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

    # flow.success()

    flow.retention = "4h"
    # flow.print()

    print("\nAS DICT")
    pprint(flow.to_dict())

    print("\nFirst Step")
    print(flow.first_step)

    print("\nLast Step")
    print(flow.last_step)

    print("\nAS Json")
    json_text1 = flow.to_json()
    flow.from_json(json_text1)
    json_text2 = flow.to_json()

    print(json_text1==json_text2)
    
    print(json_text2)

    print(f"Search {search_key}")
    flow.lookup_key = lookup_key

    from postgres_utils import get_default_engine

    # kubectl port-forward svc/postgresql 5432:5432 -n corporate-it-postgresql
    os.environ["PG_USER"] = "postgres"
    password=os.environ["PG_PASSWORD"] = "admin"
    db=os.environ["PG_DATABASE"] = "lakehouse"
    host=os.environ["PG_HOST"] = "localhost"
    port=os.environ.get("PG_PORT","5432")
    user, password, db, schema, host, port, engine = get_default_engine()

    # flow = DataFlow.from_backingstore(engine, external_reference_id="3923c671-6a17-4b6c-9fc8-cf91c1d6c2a7")
    # flow = DataFlow.from_backingstore(engine, external_reference_id="58c89484-8140-45b7-a85e-0f9623955d04")
    # flow = flow.from_backingstore(engine, external_reference_id="3923c671-6a17-4b6c-9fc8-cf91c1d6c2a7")
    # flow.from_backingstore(engine, external_reference_id="58c89484-8140-45b7-a85e-0f9623955d04")

    # status = "COMPLETED"
    # status = "SUCCESS"
    flow_persited = DataFlow.from_backingstore(engine, lookup_key=search_key, status=status)
    if flow_persited:
        flow = flow_persited
        flow.closed()
        print(f"Dataflow found search_key={search_key} and status={status}")
        print(flow.to_json())
        flow.to_backingstore(engine)
    else:
        print(f"No dataflow found with lookup_key={lookup_key} and status={status}")
        flow.open()
        flow.to_backingstore(engine)
    # flow.to_backingstore(engine)

if __name__ == "__main__":
    main()