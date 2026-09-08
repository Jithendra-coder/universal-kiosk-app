import pytest

import schema_compat


def test_schema_compatibility_executes_order_counter_objects_in_dependency_order(monkeypatch):
    class RecordingConnection:
        def __init__(self):
            self.statements = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, statement):
            self.statements.append(statement.lower())
            return self

        def fetchall(self):
            return [(column,) for column in schema_compat.ANALYTICS_ORDER_COLUMNS]

        def commit(self):
            return None

        def rollback(self):
            return None

    connection = RecordingConnection()
    monkeypatch.setattr(schema_compat, "connect", lambda _database_url: connection)

    schema_compat.ensure_schema_compatibility("postgresql://unused")

    table_index = next(
        index
        for index, statement in enumerate(connection.statements)
        if "create table if not exists order_counters" in statement
    )
    function_index = next(
        index
        for index, statement in enumerate(connection.statements)
        if "create or replace function next_order_number" in statement
    )

    assert table_index < function_index
    assert "insert into order_counters" in connection.statements[function_index]


def test_analytics_schema_contract_rejects_missing_order_columns():
    class Connection:
        def execute(self, _statement):
            return self

        def fetchall(self):
            return [("id",), ("status",)]

    with pytest.raises(schema_compat.SchemaContractError, match="payment_method"):
        schema_compat.assert_analytics_order_schema(Connection())
