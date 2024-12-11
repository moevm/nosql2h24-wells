from fastapi import HTTPException

from app.database import db


def create_courtyard(courtyard_data: dict):
    query = """
    CREATE (c:Courtyard {title: $title, created_at: timestamp()})
    WITH c
    UNWIND $houses AS address
    MERGE (h:House {address: address})
    MERGE (h)-[:BOUNDS]->(c)
    RETURN elementId(c) AS id, c.title AS title, c.created_at AS created_at, 
        collect(h.address) AS houses
    """
    result = db.query(query, courtyard_data)
    courtyard_node = result[0]

    coordinates = courtyard_data.get("coordinates", [])
    coords_ids = []

    for coord_data in coordinates:
        coord_query = """
        CREATE (coord:Coordinate {longitude: $longitude, latitude: $latitude})
        RETURN elementId(coord) AS coord_id
        """
        coord_result = db.query(coord_query, coord_data)
        coords_ids.append(coord_result[0]["coord_id"])

    for i in range(len(coords_ids) - 1):
        db.query("""
        MATCH (start:Coordinate), (end:Coordinate)
        WHERE elementId(start) = $start_id AND elementId(end) = $end_id
        CREATE (start)-[:NEXT]->(end)
        """, {"start_id": coords_ids[i], "end_id": coords_ids[i + 1]})

    db.query("""
    MATCH (c:Courtyard), (coord:Coordinate)
    WHERE elementId(c) = $courtyard_id AND elementId(coord) = $coord_id
    MERGE (c)-[:LOCATED_AT]->(coord)
    """, {"courtyard_id": courtyard_node['id'], "coord_id": coords_ids[0]})

    return {
        "courtyard": courtyard_node,
        "houses": courtyard_data["houses"],
        "coordinates": [{"longitude": coord["longitude"], "latitude": coord["latitude"]} for coord in coordinates]
    }


def get_courtyard_by_title(title: str):
    result = db.query("""
    MATCH (c:Courtyard)
    WHERE c.title = $title
    RETURN elementId(c) AS id, c.title AS title, c.created_at AS created_at
    """, {"title": title})

    if not result or len(result) == 0:
        return None
    return result[0]


def get_courtyard_by_id(courtyard_id: str):
    result = db.query("""
    MATCH (c:Courtyard)<-[:BOUNDS]-(h:House)
    MATCH (c)-[:LOCATED_AT]->(start:Coordinate)
    MATCH (start)-[:NEXT*0..]->(coords:Coordinate)
    OPTIONAL MATCH (c)<-[v:VISITED]-(u:User)
    WITH c, collect(DISTINCT h.address) AS houses, 
        collect(DISTINCT {longitude: coords.longitude, latitude: coords.latitude}) AS coordinates,
        count(DISTINCT u) AS visits_count, 
        avg(v.rating) AS average_rating
    WHERE elementId(c) = $courtyard_id
    RETURN elementId(c) AS id, c.title AS title, c.created_at AS created_at, 
        houses, coordinates, visits_count, average_rating
    """, {"courtyard_id": courtyard_id})

    if not result or len(result) == 0:
        raise HTTPException(status_code=404, detail="Courtyard not found")
    return result[0]


def search_courtyards(title: str = None, address: str = None,
                      rating_from: float = None, rating_to: float = None,
                      longitude_from: float = None, longitude_to: float = None,
                      latitude_from: float = None, latitude_to: float = None,
                      limit: int = 10, skip: int = 0):
    filters, filter_params = get_courtyards_filters(title=title, address=address,
                                                    rating_from=rating_from, rating_to=rating_to,
                                                    longitude_from=longitude_from, longitude_to=longitude_to,
                                                    latitude_from=latitude_from, latitude_to=latitude_to)
    filter_query = " AND ".join(filters) if filters else "1=1"

    query = """
    MATCH (c:Courtyard)<-[:BOUNDS]-(h:House)
    MATCH (c)-[:LOCATED_AT]->(start:Coordinate)
    MATCH (start)-[:NEXT*0..]->(coords:Coordinate)
    OPTIONAL MATCH (c)<-[v:VISITED]-(u:User)
    WITH c, h, coords, coalesce(avg(v.rating), 0) AS average_rating, count(DISTINCT u) AS visitors_count
    WHERE """ + filter_query + """ 
    RETURN elementId(c) AS id, 
           c.title AS title, 
           c.created_at AS created_at, 
           collect(DISTINCT {address: h.address}) AS houses,
           collect(DISTINCT {longitude: coords.longitude, latitude: coords.latitude}) AS coordinates, 
           visitors_count,
           average_rating
    SKIP $skip LIMIT $limit
    """

    return db.query(query, {
        **filter_params,
        "limit": limit,
        "skip": skip
    })


def get_courtyards_filters(title: str = None, address: str = None,
                           rating_from: float = None, rating_to: float = None,
                           longitude_from: float = None, longitude_to: float = None,
                           latitude_from: float = None, latitude_to: float = None):
    filters = []
    if title:
        filters.append("toLower(c.title) CONTAINS toLower($title)")
    if address:
        filters.append("toLower(h.address) CONTAINS toLower($address)")
    if rating_from is not None:
        filters.append("average_rating >= $rating_from")
    if rating_to is not None:
        filters.append("average_rating <= $rating_to")
    if longitude_from is not None:
        filters.append("coords.longitude >= $longitude_from")
    if longitude_to is not None:
        filters.append("coords.longitude <= $longitude_to")
    if latitude_from is not None:
        filters.append("coords.latitude >= $latitude_from")
    if latitude_to is not None:
        filters.append("coords.latitude <= $latitude_to")

    return filters, {
        "title": title,
        "address": address,
        "longitude_from": longitude_from,
        "longitude_to": longitude_to,
        "latitude_from": latitude_from,
        "latitude_to": latitude_to,
        "rating_from": rating_from,
        "rating_to": rating_to,
    }
