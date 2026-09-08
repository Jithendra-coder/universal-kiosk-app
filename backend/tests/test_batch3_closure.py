from services.qr_service import destination_url, _matrix
from services.version_service import _domains


def test_qr_destination_uses_business_slug_and_matrix_has_finders():
    url = destination_url({"slug": "demo"}, {"destination_type": "takeaway"})
    assert url == "/kiosk/demo?order_type=takeaway"
    matrix = _matrix(url)
    assert len(matrix) == 29 and len(matrix[0]) == 29
    assert matrix[0][0] == matrix[0][6] == matrix[6][0] == 1


def test_version_comparison_is_domain_grouped():
    left = {"business": {"name": "new"}, "products": [{"id": "p1", "name": "new"}]}
    right = {"business": {"name": "old"}, "products": [{"id": "p1", "name": "old"}]}
    domains = {row["key"]: row["changed"] for row in _domains(left, right)}
    assert domains["business"] == 1
    assert domains["products"] == 1
