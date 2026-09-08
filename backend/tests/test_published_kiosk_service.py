from services import kiosk_service


def test_live_kiosk_uses_published_configuration_with_current_stock(monkeypatch):
    business = {"id": "00000000-0000-0000-0000-000000000001", "slug": "demo", "name": "Draft name", "is_active": True}
    published = {
        "business": {"id": business["id"], "slug": "demo", "name": "Live name", "display_show_unavailable": False},
        "categories": [{"id": "c1", "is_active": True}],
        "products": [{"id": "p1", "name": "Live item", "price": 10, "is_available": True, "menu_status": "shown", "track_stock": True}],
        "modifier_groups": [],
        "modifier_options": [],
    }
    monkeypatch.setattr(kiosk_service.cache_service, "get_menu", lambda _slug: None)
    monkeypatch.setattr(kiosk_service.cache_service, "set_menu", lambda *_args: None)
    monkeypatch.setattr(kiosk_service, "get_business_by_slug", lambda *_args: business)
    monkeypatch.setattr(kiosk_service.setup_service, "live_configuration", lambda *_args: published)
    monkeypatch.setattr(kiosk_service, "list_products", lambda *_args, **_kwargs: [{"id": "p1", "price": 999, "stock_quantity": 4, "sold_today": 2}])
    monkeypatch.setattr(kiosk_service.pin_service, "public_lock_state", lambda _business: {"enabled": False})
    monkeypatch.setattr(kiosk_service.payment_service, "public_payment_summary", lambda *_args: {"enabled_methods": []})

    payload = kiosk_service.get_kiosk_payload(object(), "demo")

    assert payload["business"]["name"] == "Live name"
    assert payload["products"][0]["price"] == 10
    assert payload["products"][0]["stock_quantity"] == 4
