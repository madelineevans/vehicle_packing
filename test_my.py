from fastapi.testclient import TestClient
from main import app
from solution import search_grouped
from models import Vehicle

client = TestClient(app)

def normalize(results):
    return sorted(
        [{**r, "listing_ids": sorted(r["listing_ids"])} for r in results],
        key=lambda x: x["location_id"]
    )

def test_search_grouped_multi_lane_packing():
    # width=30 => 3 lanes, lane capacity = length
    grouped = {
        "locM": [
            {"id": "m1", "length": 10, "width": 30, "location_id": "locM", "price_in_cents": 120}
        ]
    }
    vehicles_sorted = [Vehicle(length=10, quantity=3)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "locM", "listing_ids": ["m1"], "total_price_in_cents": 120}
    ]
    assert normalize(result) == normalize(actual)

def test_search_grouped_exact_boundary_fit():
    # vehicle length equals lane capacity exactly (<= should be allowed)
    grouped = {
        "locE": [
            {"id": "e1", "length": 20, "width": 10, "location_id": "locE", "price_in_cents": 90}
        ]
    }
    vehicles_sorted = [Vehicle(length=20, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "locE", "listing_ids": ["e1"], "total_price_in_cents": 90}
    ]
    assert normalize(result) == normalize(actual)

def test_search_grouped_orientation_matters_negative():
    # Non-rotated fails (cap=10), rotated also fails (cap=10) -> no solution
    grouped = {
        "locN": [
            {"id": "n1", "length": 10, "width": 10, "location_id": "locN", "price_in_cents": 50}
        ]
    }
    vehicles_sorted = [Vehicle(length=20, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    assert result == []

def test_search_grouped_two_listings_needed_same_location():
    # Need two listings to cover two vehicles
    grouped = {
        "loc2": [
            {"id": "a", "length": 15, "width": 10, "location_id": "loc2", "price_in_cents": 70},
            {"id": "b", "length": 10, "width": 10, "location_id": "loc2", "price_in_cents": 40}
        ]
    }
    vehicles_sorted = [Vehicle(length=15, quantity=1), Vehicle(length=10, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "loc2", "listing_ids": ["a", "b"], "total_price_in_cents": 110}
    ]
    assert normalize(result) == normalize(actual)

def test_search_grouped_prefer_cheapest_combo_over_bigger_single():
    # One big listing fits all but is pricier than two cheaper small ones
    grouped = {
        "locC": [
            {"id": "big", "length": 30, "width": 30, "location_id": "locC", "price_in_cents": 400},
            {"id": "s1", "length": 20, "width": 20, "location_id": "locC", "price_in_cents": 150},
            {"id": "s2", "length": 10, "width": 20, "location_id": "locC", "price_in_cents": 80}
        ]
    }
    vehicles_sorted = [Vehicle(length=20, quantity=2), Vehicle(length=10, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "locC", "listing_ids": ["s1", "s2"], "total_price_in_cents": 230}
    ]
    assert normalize(result) == normalize(actual)

def test_search_grouped_tie_on_price_multiple_locations():
    # Two locations with equal total price — both should appear (sorted later by price in API)
    grouped = {
        "locX": [
            {"id": "x1", "length": 10, "width": 20, "location_id": "locX", "price_in_cents": 100}
        ],
        "locY": [
            {"id": "y1", "length": 10, "width": 20, "location_id": "locY", "price_in_cents": 100}
        ]
    }
    vehicles_sorted = [Vehicle(length=10, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "locX", "listing_ids": ["x1"], "total_price_in_cents": 100},
        {"location_id": "locY", "listing_ids": ["y1"], "total_price_in_cents": 100}
    ]
    assert normalize(result) == normalize(actual)

def test_search_grouped_multi_lane_across_lengths():
    # width=20 => 2 lanes; pack 10 and 20-length vehicles if rotated appropriately
    grouped = {
        "locL": [
            {"id": "l1", "length": 10, "width": 20, "location_id": "locL", "price_in_cents": 160}
        ]
    }
    vehicles_sorted = [Vehicle(length=10, quantity=1), Vehicle(length=10, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "locL", "listing_ids": ["l1"], "total_price_in_cents": 160}
    ]
    assert normalize(result) == normalize(actual)

def test_search_grouped_quantity_cap_edge():
    # Max quantity sum = 5; ensure all five can be placed when feasible
    grouped = {
        "locQ": [
            {"id": "q1", "length": 50, "width": 20, "location_id": "locQ", "price_in_cents": 300}
        ]
    }
    vehicles_sorted = [Vehicle(length=10, quantity=5)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "locQ", "listing_ids": ["q1"], "total_price_in_cents": 300}
    ]
    assert normalize(result) == normalize(actual)

def test_search_grouped_dominated_listing_ignored():
    # l_bad is strictly worse (shorter and more expensive) than l_good; ensure solution uses l_good
    grouped = {
        "locD": [
            {"id": "l_bad",  "length": 10, "width": 20, "location_id": "locD", "price_in_cents": 200},
            {"id": "l_good", "length": 20, "width": 20, "location_id": "locD", "price_in_cents": 150}
        ]
    }
    vehicles_sorted = [Vehicle(length=20, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [
        {"location_id": "locD", "listing_ids": ["l_good"], "total_price_in_cents": 150}
    ]
    assert normalize(result) == normalize(actual)

def test_api_post_integration_happy_path():
    # end-to-end: POST to the API root; schema/shape sanity
    payload = [{"length": 10, "quantity": 1}]
    resp = client.post("/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:  # if your real listings.json has matches
        assert "location_id" in data[0]
        assert "listing_ids" in data[0]
        assert "total_price_in_cents" in data[0]


def test_search_grouped_fail_insufficient_total_lane_capacity():
    """
    Fail because total lane capacity (sum of lanes * lane_cap) is too small,
    even though each vehicle would fit a lane individually.
    width=20 -> 2 lanes, lane_cap=10 => total capacity = 20 < required 30
    """
    grouped = {
        "locFAIL1": [
            {"id": "f1", "length": 10, "width": 20, "location_id": "locFAIL1", "price_in_cents": 100}
        ]
    }
    vehicles_sorted = [Vehicle(length=10, quantity=3)]  # needs total length 30
    result = search_grouped(grouped, vehicles_sorted)
    assert result == []

def test_search_grouped_fail_longest_vehicle_exceeds_lane_cap():
    """
    Fail because the longest vehicle exceeds the best lane capacity of the location,
    regardless of total capacity.
    width=30 -> 3 lanes, lane_cap=10, but vehicle length 20 > 10 (no lane can host it)
    """
    grouped = {
        "locFAIL2": [
            {"id": "f2", "length": 10, "width": 30, "location_id": "locFAIL2", "price_in_cents": 150}
        ]
    }
    vehicles_sorted = [Vehicle(length=20, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    assert result == []

# ---------- API SORTING / UNIQUENESS ----------

def test_api_results_sorted_by_total_price():
    """
    Integration-ish: hit the real API.
    If the dataset returns >=2 results for a simple request,
    verify they are sorted by total_price_in_cents ascending.
    """
    payload = [{"length": 10, "quantity": 1}]
    resp = client.post("/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Only assert sorting when there are multiple results
    if isinstance(data, list) and len(data) >= 2:
        prices = [r["total_price_in_cents"] for r in data]
        assert prices == sorted(prices)

def test_search_grouped_unique_result_per_location():
    """
    Ensure only one result per location_id even if multiple combos could fit.
    Here, either 'a' alone (length 20) or 'b'+'c' (10+10) could satisfy the need,
    but we should return exactly one (the cheapest).
    """
    grouped = {
        "locU": [
            {"id": "a", "length": 20, "width": 20, "location_id": "locU", "price_in_cents": 120},
            {"id": "b", "length": 10, "width": 20, "location_id": "locU", "price_in_cents": 50},
            {"id": "c", "length": 10, "width": 20, "location_id": "locU", "price_in_cents": 40},
        ],
        "locV": [
            {"id": "v1", "length": 20, "width": 30, "location_id": "locV", "price_in_cents": 200}
        ]
    }
    vehicles_sorted = [Vehicle(length=10, quantity=3)]
    result = search_grouped(grouped, vehicles_sorted)

    # Expect one result per location, using the cheapest combo:
    # locU → b+c (50+40=90) beats a (120); locV → v1 (200)
    actual = [
        {"location_id": "locU", "listing_ids": ["b", "c"], "total_price_in_cents": 90},
        {"location_id": "locV", "listing_ids": ["v1"], "total_price_in_cents": 200},
    ]
    assert normalize(result) == normalize(actual)

# ---------- EXTRA PACKING SANITY ----------

def test_search_grouped_pack_within_single_lane_exact_sum():
    """
    Single lane with cap=30 (length=30,width=10). Vehicles 20 and 10 must share the same lane.
    Ensures your packing places multiple vehicles in one lane when sums match capacity.
    """
    grouped = {
        "locS": [
            {"id": "s1", "length": 30, "width": 10, "location_id": "locS", "price_in_cents": 180}
        ]
    }
    vehicles_sorted = [Vehicle(length=20, quantity=1), Vehicle(length=10, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)
    actual = [{"location_id": "locS", "listing_ids": ["s1"], "total_price_in_cents": 180}]
    assert normalize(result) == normalize(actual)

def test_search_grouped_multi_listing_vs_one_big_list_tie_on_price():
    """
    If a single big listing equals the price of two smaller listings, either solution may be chosen.
    This test ensures your algorithm returns exactly one cheapest solution and is deterministic.
    """
    grouped = {
        "locT": [
            {"id": "big", "length": 30, "width": 30, "location_id": "locT", "price_in_cents": 300},
            {"id": "s1", "length": 20, "width": 20, "location_id": "locT", "price_in_cents": 150},
            {"id": "s2", "length": 10, "width": 20, "location_id": "locT", "price_in_cents": 150},
        ]
    }
    vehicles_sorted = [Vehicle(length=20, quantity=2), Vehicle(length=10, quantity=1)]
    result = search_grouped(grouped, vehicles_sorted)

    # Either ['big'] (300) or ['s1','s2'] (300) is acceptable,
    # but there must be exactly one result for locT with total_price_in_cents == 300.
    assert len(result) == 1
    assert result[0]["location_id"] == "locT"
    assert result[0]["total_price_in_cents"] == 300
    # Optionally check determinism by asserting which combo you expect your solver to pick.
    # For example, if you prefer fewer listings on price ties:
    # assert result[0]["listing_ids"] == ["big"]