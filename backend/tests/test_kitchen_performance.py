from uuid import uuid4

from services import kitchen_service


class KitchenClient:
    def __init__(self):
        self.calls = []

    def fetch_all(self, query, params):
        self.calls.append((query, params))
        if "kitchen_order_states" in query:
            return [{"order_id": "order-1", "stage": "preparing", "is_held": False, "hold_reason": None, "held_at": None, "updated_at": "2026-08-08T10:00:00+00:00"}]
        if "kitchen_item_states" in query:
            return [{"order_id": "order-1", "order_item_id": "item-1", "completed_quantity": 1, "updated_at": "2026-08-08T10:00:00+00:00"}]
        raise AssertionError(query)


def test_board_batches_kitchen_state_reads_for_all_orders(monkeypatch):
    business = {"id": str(uuid4()), "kiosk_order_settings": {}}
    device = {"id": "device-1"}
    orders = [
        {"id": "order-1", "status": "preparing", "placed_at": "2026-08-08T10:00:00+00:00", "order_items": [{"id": "item-1", "quantity": 2}]},
        {"id": "order-2", "status": "pending", "placed_at": "2026-08-08T10:00:00+00:00", "order_items": [{"id": "item-2", "quantity": 1}]},
    ]
    client = KitchenClient()
    monkeypatch.setattr(kitchen_service, "_kitchen", lambda *_args: (business, device))
    monkeypatch.setattr(kitchen_service.order_service, "list_orders", lambda *_args, **_kwargs: orders)
    monkeypatch.setattr(kitchen_service, "serialize_business_for_response", lambda value: value)

    result = kitchen_service.board(client, None)

    assert len(client.calls) == 2
    assert client.calls[0][1]["order_ids"] == ["order-1", "order-2"]
    assert result["orders"][0]["items"][0]["completed_quantity"] == 1
    assert result["orders"][1]["items"][0]["kitchen_status"] == "pending"
