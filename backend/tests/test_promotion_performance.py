from uuid import uuid4

from services import promotion_service


class PromotionClient:
    def __init__(self, first_id, second_id):
        self.first_id = str(first_id)
        self.second_id = str(second_id)
        self.calls = []

    def fetch_all(self, query, params):
        self.calls.append((query, params))
        if "from kiosk_promotions" in query:
            return [{"id": self.first_id, "name": "Breakfast"}, {"id": self.second_id, "name": "Lunch"}]
        if "kiosk_promotion_targets" in query:
            return [{"promotion_id": self.first_id, "target_type": "product", "target_id": "product-1"}]
        if "kiosk_promotion_locations" in query:
            return [{"promotion_id": self.second_id, "location_id": "location-1"}]
        if "kiosk_promotion_placements" in query:
            return [{"promotion_id": self.first_id, "placement": "deals_category"}]
        raise AssertionError(query)


def test_list_promotions_uses_constant_relation_query_count(monkeypatch):
    business_id = uuid4()
    first_id, second_id = uuid4(), uuid4()
    client = PromotionClient(first_id, second_id)
    monkeypatch.setattr(promotion_service, "_access", lambda *_args: {})

    result = promotion_service.list_promotions(client, business_id, uuid4())

    assert len(client.calls) == 4
    assert client.calls[1][1]["ids"] == [str(first_id), str(second_id)]
    assert result["promotions"] == [
        {"id": str(first_id), "name": "Breakfast", "targets": [{"target_type": "product", "target_id": "product-1"}], "location_ids": [], "placements": ["deals_category"]},
        {"id": str(second_id), "name": "Lunch", "targets": [], "location_ids": ["location-1"], "placements": []},
    ]


def test_list_promotions_with_no_rows_skips_relation_queries(monkeypatch):
    class EmptyClient:
        def __init__(self): self.calls = 0
        def fetch_all(self, _query, _params): self.calls += 1; return []

    client = EmptyClient()
    monkeypatch.setattr(promotion_service, "_access", lambda *_args: {})

    assert promotion_service.list_promotions(client, uuid4(), uuid4()) == {"promotions": []}
    assert client.calls == 1
