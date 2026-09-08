from database import DbClient


class Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class RecordingConnection:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        rows = [
            {key.removeprefix("row_").split("_", 1)[1]: value for key, value in params.items() if key.startswith(f"row_{index}_")}
            for index in range(sum(key.startswith("row_") and key.endswith("_business_id") for key in params))
        ]
        return Result(rows)


def test_matching_row_shapes_use_one_bounded_multi_row_insert():
    connection = RecordingConnection()
    client = DbClient(connection)

    result = client.table("order_items").insert([
        {"business_id": "business-a", "order_id": "order-1", "quantity": 1},
        {"business_id": "business-a", "order_id": "order-2", "quantity": 2},
    ]).execute()

    assert len(connection.calls) == 1
    sql, params = connection.calls[0]
    assert 'insert into "order_items"' in sql
    assert "), (" in sql
    assert params["row_0_order_id"] == "order-1"
    assert params["row_1_order_id"] == "order-2"
    assert [row["quantity"] for row in result.data] == [1, 2]


def test_mismatched_row_shapes_keep_the_existing_single_row_behavior():
    connection = RecordingConnection()
    client = DbClient(connection)

    client.table("order_items").insert([
        {"business_id": "business-a", "order_id": "order-1"},
        {"business_id": "business-a", "order_id": "order-2", "notes": "No onions"},
    ]).execute()

    assert len(connection.calls) == 2
