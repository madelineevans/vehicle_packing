from models import Vehicle
import json

def can_fit(listings: list, vehicles: list, ids: list, total_price: int):
    if vehicles == []:
        return ids, total_price
    if listings == []:
        return None, float('inf')
    best_ids = None
    best_price = float('inf')

    for listing in listings:              #for each listing in that location
        if listing.get('length') >= vehicles[0].length:
            tempList = [Vehicle(length=v.length, quantity=v.quantity) for v in vehicles]  # deep copy
            for i in range(int(listing.get('width'))//10):
                lenLeft = listing.get('length')
                idx = 0
                while lenLeft > 0 and idx < len(tempList):
                    v = tempList[idx]
                    if v.length <= lenLeft and v.quantity > 0:
                        lenLeft -= v.length
                        v.quantity -= 1
                        if v.quantity == 0:
                            tempList.pop(idx)
                    else:
                        idx += 1
            # Always try the recursive call, even if tempList is empty
            ids_rec, price = can_fit([l for l in listings if l["id"] != listing["id"]], tempList, ids + [listing['id']], total_price + listing['price_in_cents'])
            if ids_rec is not None and price < best_price:
                best_ids = ids_rec
                best_price = price
    # Only return if all vehicles are fit (i.e., best_ids is not None)
    return best_ids, best_price


def search_grouped(grouped: dict, vehicles: list):
    result = [] #final results(just the min price per location)

    for location_id, listings in grouped.items(): #for each location
        ids, price = can_fit(listings, vehicles, [], 0)
        
        #loc_min = min(fits_loc.values(), key=lambda x: x[0]["price_in_cents"])
        if ids is not None:
            result.append({
                "location_id": location_id,
                "listing_ids": ids,
                "total_price_in_cents": price
            })
    
    result = sorted(result, key=lambda x: x["total_price_in_cents"])
    return result

def load_grouped_listings():
    with open('listings.json', 'r') as f:
        listings = json.load(f)
    grouped = {}
    for item in listings:
        if item.get("location_id") not in grouped:
            grouped[item["location_id"]] = []
        grouped[item["location_id"]].append(item)
    return grouped