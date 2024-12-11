from fastapi import HTTPException
from app.courtyard_service import get_courtyards_filters, get_courtyard_by_id, get_courtyard_by_title
from app.database import db
import bcrypt


def get_user_by_nickname(nickname: str, with_password: bool = False):
    result = db.query(
        f"""
        MATCH (u:User)
        WHERE u.nickname = $nickname
        OPTIONAL MATCH (u)-[:VISITED]->(c:Courtyard)
        RETURN elementId(u) AS id, u.nickname AS nickname, u.first_name AS first_name, u.last_name AS last_name, 
            u.patronymic AS patronymic, u.avatar_url AS avatar_url, u.created_at AS created_at,
            {"u.password AS password," if with_password else ""}
            count(DISTINCT c) AS visits_count
        """,
        {"nickname": nickname}
    )
    if not result or len(result) == 0:
        return None
    return result[0]


def authenticate_user(nickname, password):
    if not nickname or not password:
        raise HTTPException(status_code=400, detail="Nickname and password are required")

    user = get_user_by_nickname(nickname, with_password=True)

    if not user:
        return None

    if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        del user['password']
        return user

    raise HTTPException(status_code=401, detail="Invalid credentials")


def create_user(user_data: dict, hash_password=True):
    password = user_data['password']
    if hash_password:
        password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    return db.query(
        """
        CREATE (u:User {
            last_name: $last_name, 
            first_name: $first_name, 
            patronymic: $patronymic,
            nickname: $nickname, 
            password: $password, 
            avatar_url: $avatar_url, 
            created_at: timestamp()
        })
        RETURN elementId(u) AS id, u.nickname AS nickname, u.first_name AS first_name, u.last_name AS last_name, 
            u.patronymic AS patronymic, u.avatar_url AS avatar_url, u.created_at AS created_at
        """,
        {
            'last_name': user_data['last_name'] if 'last_name' in user_data else '',
            'first_name': user_data['first_name'] if 'first_name' in user_data else '',
            'patronymic': user_data['patronymic'] if 'patronymic' in user_data else '',
            'avatar_url': user_data['avatar_url'] if 'avatar_url' in user_data else '',
            'nickname': user_data['nickname'],
            'password': password,
        }
    )[0]


def get_user_by_id(user_id: str):
    result = db.query(
        """
        MATCH (u:User)
        WHERE elementId(u) = $user_id
        OPTIONAL MATCH (u)-[:VISITED]->(c:Courtyard)
        RETURN elementId(u) AS id, u.nickname AS nickname, u.first_name AS first_name, u.last_name AS last_name, 
            u.patronymic AS patronymic, u.avatar_url AS avatar_url, u.created_at AS created_at,
            count(DISTINCT c) AS visits_count
        """,
        {"user_id": user_id}
    )
    if not result or len(result) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return result[0]


def update_user(user_id: str, user_data: dict):
    get_user_by_id(user_id)  # check user exists

    if 'nickname' in user_data:
        existing = get_user_by_nickname(user_data['nickname'])
        if existing and existing['id'] != user_id:
            print(existing['id'], user_id)
            raise HTTPException(status_code=401, detail="User with this nickname already exists")

    return db.query(
        f"""
        MATCH (u:User) 
        WHERE elementId(u) = $user_id
        SET u.last_name = COALESCE($last_name, u.first_name), 
            u.first_name = COALESCE($first_name, u.first_name), 
            u.patronymic = COALESCE($patronymic, u.first_name),
            u.nickname = COALESCE($nickname, u.first_name), 
            u.avatar_url = COALESCE($avatar_url, u.first_name)
        RETURN elementId(u) AS id, u.nickname AS nickname, u.first_name AS first_name, u.last_name AS last_name, 
            u.patronymic AS patronymic, u.avatar_url AS avatar_url, u.created_at AS created_at
        """,
        {
            'user_id': user_id,
            'last_name': user_data['last_name'] if 'last_name' in user_data else None,
            'first_name': user_data['first_name'] if 'first_name' in user_data else None,
            'patronymic': user_data['patronymic'] if 'patronymic' in user_data else None,
            'avatar_url': user_data['avatar_url'] if 'avatar_url' in user_data else None,
            'nickname': user_data['nickname'] if 'nickname' in user_data else None,
        }
    )[0]


def validate_visit(visit: dict) -> dict:
    if 'user_id' in visit:
        user = get_user_by_id(visit['user_id'])
    else:
        user = get_user_by_nickname(visit['username'])

    if 'courtyard_id' in visit:
        courtyard = get_courtyard_by_id(visit['courtyard_id'])
    else:
        courtyard = get_courtyard_by_title(visit['courtyard_title'])

    existing = search_visits(courtyard_id=courtyard['id'], user_id=user['id'])
    if len(existing) > 0:
        raise HTTPException(status_code=401, detail="This visit is already exists")

    if 'comment' not in visit:
        visit['comment'] = ''

    visit['rating'] = int(visit['rating'])

    return visit


def visit_courtyard(visit: dict):
    visit = validate_visit(visit)
    return db.query(
        """
        MATCH (u:User) WHERE elementId(u) = $user_id
        MATCH (c:Courtyard) WHERE elementId(c) = $courtyard_id
        CREATE (u)-[:VISITED {visited_at: $visited_at, comment: $comment, rating: $rating}]->(c)
        """,
        visit
    )


def visit_courtyard_by_titles(visit: dict):
    visit = validate_visit(visit)
    return db.query(
        """
        MATCH (u:User) WHERE u.nickname = $username
        MATCH (c:Courtyard) WHERE c.title = $courtyard_title
        CREATE (u)-[:VISITED {visited_at: $visited_at, comment: $comment, rating: $rating}]->(c)
        """,
        visit
    )


def search_users(first_name: str = None, last_name: str = None, patronymic: str = None, nickname: str = None,
                 min_visits: int = None, max_visits: int = None, limit: int = 10, skip: int = 0):
    filters, filter_params = get_user_filters(first_name=first_name, last_name=last_name, patronymic=patronymic,
                                              nickname=nickname, min_visits=min_visits, max_visits=max_visits)

    filter_query = " AND ".join(filters) if filters else "1=1"

    query = f"""
    MATCH (u:User)
    OPTIONAL MATCH (u)-[v:VISITED]->(c:Courtyard)
    WITH u, collect(DISTINCT c) AS courtyards
    WITH u, size(courtyards) AS visited_courtyards
    WHERE {filter_query}
        RETURN elementId(u) AS id, u.nickname AS nickname, u.first_name AS first_name, u.last_name AS last_name, 
            u.patronymic AS patronymic, u.avatar_url AS avatar_url, u.created_at AS created_at,
            visited_courtyards
    SKIP $skip LIMIT $limit
    """
    return db.query(query, {
        **filter_params,
        "limit": limit,
        "skip": skip
    })


def get_user_filters(first_name: str = None, last_name: str = None, patronymic: str = None, nickname: str = None,
                     min_visits: int = None, max_visits: int = None):
    filters = []
    if first_name:
        filters.append("toLower(u.first_name) CONTAINS toLower($first_name)")
    if patronymic:
        filters.append("toLower(u.patronymic) CONTAINS toLower($patronymic)")
    if last_name:
        filters.append("toLower(u.last_name) CONTAINS toLower($last_name)")
    if nickname:
        filters.append("toLower(u.nickname) CONTAINS toLower($nickname)")
    if min_visits is not None:
        filters.append("visited_courtyards >= $min_visits")
    if max_visits is not None:
        filters.append("visited_courtyards <= $max_visits")

    return filters, {
        "first_name": first_name,
        "last_name": last_name,
        "patronymic": patronymic,
        "nickname": nickname,
        "min_visits": min_visits,
        "max_visits": max_visits,
    }


def search_visits(courtyard_id: str = None, courtyard_title: str = None, courtyard_address: str = None,
                  courtyard_rating_from: float = None, courtyard_rating_to: float = None,
                  longitude_from: float = None, longitude_to: float = None,
                  latitude_from: float = None, latitude_to: float = None,
                  user_id: str = None, user_first_name: str = None, user_last_name: str = None,
                  user_patronymic: str = None, user_nickname: str = None, min_visits: int = None,
                  max_visits: int = None,
                  visited_from: str = None, visited_to: str = None, comment_exists: bool = None,
                  comment: str = None, rating: int = None,
                  limit: int = 10, skip: int = 0):
    courtyard_filters, courtyard_params = get_courtyards_filters(title=courtyard_title, address=courtyard_address,
                                                                 rating_from=courtyard_rating_from,
                                                                 rating_to=courtyard_rating_to,
                                                                 longitude_from=longitude_from,
                                                                 longitude_to=longitude_to,
                                                                 latitude_from=latitude_from,
                                                                 latitude_to=latitude_to)
    if courtyard_id:
        courtyard_filters.append("elementId(c) = $courtyard_id")

    user_filters, user_params = get_user_filters(first_name=user_first_name, last_name=user_last_name,
                                                 patronymic=user_patronymic, nickname=user_nickname,
                                                 min_visits=min_visits, max_visits=max_visits)
    if user_id:
        user_filters.append("elementId(u) = $user_id")

    visit_filters = courtyard_filters + user_filters
    if visited_from:
        visit_filters.append("v.visited_at >= $visited_from")
    if visited_to:
        visit_filters.append("v.visited_at <= $visited_to")
    if comment_exists:
        visit_filters.append("v.comment <> \"\"")
    if comment:
        visit_filters.append("toLower(v.comment) CONTAINS toLower($comment)")
    if rating:
        visit_filters.append("v.rating = $rating")

    filter_query = " AND ".join(visit_filters) if visit_filters else "1=1"

    query = """
    MATCH (u:User)-[v:VISITED]->(c:Courtyard)
    MATCH (c)<-[:BOUNDS]-(h:House)
    WITH c, u, v, h,
         elementId(u) AS user_id, elementId(c) AS courtyard_id
    OPTIONAL MATCH (c)<-[v_all:VISITED]-(:User)
    WITH c, u, v, h, user_id, courtyard_id,
         avg(v_all.rating) AS average_rating
    OPTIONAL MATCH (u)-[:VISITED]->(unique_courtyard:Courtyard)
    WITH c, u, v, h, user_id, courtyard_id, average_rating,
        COLLECT(DISTINCT h.address) AS houses,
        COUNT(DISTINCT unique_courtyard) AS visited_courtyards
    WHERE """ + filter_query + """
    WITH v, u, user_id, courtyard_id, average_rating, c,
         collect(DISTINCT h.address) AS houses
    WITH v,
         {
             id: user_id,
             nickname: u.nickname,
             first_name: u.first_name,
             last_name: u.last_name,
             patronymic: u.patronymic,
             avatar_url: u.avatar_url,
             created_at: u.created_at
         } AS user,
         {
             id: courtyard_id,
             title: c.title,
             houses: houses,
             average_rating: average_rating,
             created_at: c.created_at
         } AS courtyard
    RETURN courtyard, user,
           v.visited_at AS visited_at,
           v.comment AS comment,
           v.rating AS rating
    ORDER BY courtyard.id, visited_at
    SKIP $skip LIMIT $limit
    """

    return db.query(query, {
        **courtyard_params,
        **user_params,
        "user_id": user_id,
        "courtyard_id": courtyard_id,
        "visited_from": visited_from,
        "visited_to": visited_to,
        "comment": comment,
        "rating": rating,
        "limit": limit,
        "skip": skip
    })


def statistic_visits(courtyard_title: str = None, courtyard_address: str = None,
                  courtyard_rating_from: float = None, courtyard_rating_to: float = None,
                  longitude_from: float = None, longitude_to: float = None,
                  latitude_from: float = None, latitude_to: float = None,
                  visited_from: str = None, visited_to: str = None, comment_exists: bool = None):
    visit_filters, courtyard_params = get_courtyards_filters(title=courtyard_title, address=courtyard_address,
                                                                 rating_from=courtyard_rating_from,
                                                                 rating_to=courtyard_rating_to,
                                                                 longitude_from=longitude_from,
                                                                 longitude_to=longitude_to,
                                                                 latitude_from=latitude_from,
                                                                 latitude_to=latitude_to)

    if visited_from:
        visit_filters.append("v.visited_at >= $visited_from")
    if visited_to:
        visit_filters.append("v.visited_at <= $visited_to")
    if comment_exists:
        visit_filters.append("v.comment <> \"\"")

    filter_query = " AND ".join(visit_filters) if visit_filters else "1=1"

    query = """
    MATCH (c:Courtyard)<-[v:VISITED]-(:User)
    WHERE """ + filter_query + """
    WITH v.visited_at AS visit_day,
         AVG(v.rating) AS average_rating,
         COUNT(v) AS visit_count,
         COUNT(CASE WHEN v.comment <> "" THEN 1 END) AS review_count
    RETURN visit_day,
           average_rating,
           visit_count,
           review_count
    ORDER BY visit_day ASC
    """

    return db.query(query, {
        **courtyard_params,
        "visited_from": visited_from,
        "visited_to": visited_to,
    })
