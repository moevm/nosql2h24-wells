import sys
import math

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import db
from app.user_service import create_user, get_user_by_id, visit_courtyard, search_users, update_user, \
    visit_courtyard_by_titles, search_visits, authenticate_user, get_user_by_nickname
from app.courtyard_service import create_courtyard, search_courtyards, get_courtyard_by_id, get_courtyard_by_title

app = FastAPI()
allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)


@app.post("/login")
async def login(request: Request):
    user_data = await request.json()
    nickname = user_data.get("nickname")
    password = user_data.get("password")
    user = authenticate_user(nickname, password)
    if not user:
        return create_user({
            "nickname": nickname,
            "password": password,
        })

    return user


@app.get("/users/{user_id}")
def get_user(user_id: str):
    return get_user_by_id(user_id)


@app.get("/users/{user_id}/visits")
def get_user_visits(courtyard_title: str = None, courtyard_address: str = None,
                    courtyard_rating: str = None, longitude_str: str = None, latitude_str: str = None,
                    user_id: str = None, visited_from: str = None, visited_to: str = None, comment_exists: bool = None,
                    comment: str = None, rating: int = None, limit: int = 10, skip: int = 0):
    return search_visits(courtyard_title=courtyard_title, courtyard_address=courtyard_address,
                         courtyard_rating=courtyard_rating, longitude_str=longitude_str, latitude_str=latitude_str,
                         user_id=user_id, visited_from=visited_from, visited_to=visited_to,
                         comment_exists=comment_exists, comment=comment, rating=rating,
                         limit=limit, skip=skip)


@app.put("/users/{user_id}")
async def update_user_profile(user_id: str, request: Request):
    user_data = await request.json()
    return update_user(user_id, user_data)


@app.get("/users")
def get_users(first_name: str = None, last_name: str = None, patronymic: str = None, nickname: str = None,
              min_visits: int = None, max_visits: int = None, limit: int = 10, skip: int = 0):
    return search_users(first_name=first_name, last_name=last_name, patronymic=patronymic, nickname=nickname,
                        min_visits=min_visits, max_visits=max_visits, limit=limit, skip=skip)


@app.post("/visits")
def visit_courtyard_by_user(visit: dict, response: Response):
    visit_courtyard(visit)
    response.status_code = 204
    return None


@app.get("/visits")
def get_visits(courtyard_id: str = None, courtyard_title: str = None, courtyard_address: str = None,
               courtyard_rating: str = None, longitude: str = None, latitude: str = None,
               user_id: str = None, user_first_name: str = None, user_last_name: str = None,
               user_patronymic: str = None, user_nickname: str = None, min_visits: int = None,
               max_visits: int = None,
               visited_from: str = None, visited_to: str = None, comment_exists: bool = None,
               comment: str = None, rating: int = None,
               limit: int = 10, skip: int = 0):
    return search_visits(courtyard_id=courtyard_id, courtyard_title=courtyard_title,
                         courtyard_address=courtyard_address,
                         courtyard_rating=courtyard_rating, longitude_str=longitude, latitude_str=latitude,
                         user_id=user_id, user_first_name=user_first_name, user_last_name=user_last_name,
                         user_patronymic=user_patronymic, user_nickname=user_nickname, min_visits=min_visits,
                         max_visits=max_visits,
                         visited_from=visited_from, visited_to=visited_to, comment_exists=comment_exists,
                         comment=comment, rating=rating,
                         limit=limit, skip=skip)


@app.get("/courtyards/{courtyard_id}/visits")
def get_courtyard_visits(courtyard_id: str, limit: int = 10, skip: int = 0):
    return search_visits(courtyard_id=courtyard_id,
                         limit=limit, skip=skip)


@app.get("/courtyards/{courtyard_id}")
def get_courtyard(courtyard_id: str):
    return get_courtyard_by_id(courtyard_id)


@app.post("/courtyards")
def create_new_courtyard(courtyard_data: dict):
    return create_courtyard(courtyard_data)


@app.get("/courtyards")
def get_courtyards(title: str = None, address: str = None, rating: str = None, longitude: str = None,
                   latitude: str = None, limit: int = 10, skip: int = 0):
    return search_courtyards(title=title, address=address, rating_str=rating, longitude_str=longitude,
                             latitude_str=latitude, limit=limit, skip=skip)


@app.post("/import")
def import_data(data: dict):
    db.begin()
    try:
        if 'users' in data:
            for user in data['users']:
                exists = get_user_by_nickname(user['nickname'])
                if not exists:
                    create_user(user, hash_password=False)

        if 'courtyards' in data:
            for courtyard in data['courtyards']:
                exists = get_courtyard_by_title(courtyard['title'])
                if not exists:
                    create_courtyard(courtyard)

        if 'visits' in data:
            for visit in data['visits']:
                user = get_user_by_nickname(visit['username'])
                courtyard = get_courtyard_by_title(visit['courtyard_title'])
                if not user:
                    raise HTTPException(status_code=404, detail=f"User {visit['username']} not found")
                if not courtyard:
                    raise HTTPException(status_code=404, detail=f"Courtyard {visit['courtyard_title']} not found")

                existing = search_visits(courtyard_id=courtyard['id'], user_id=user['id'])
                if len(existing) == 0:
                    visit_courtyard_by_titles(visit)
    except Exception as e:
        db.rollback()
        raise e
    db.commit()

    return None


@app.get("/export")
def export_data():
    result = {
        'users': search_users(limit=sys.maxsize),
        'courtyards': search_courtyards(limit=sys.maxsize),
        'visits': [],
    }
    visits = search_visits(limit=sys.maxsize)
    for visit in visits:
        result['visits'].append({
            "username": visit['user']['nickname'],
            "courtyard_title": visit['courtyard']['title'],
            "visited_at": visit['visited_at'],
            "rating": visit['rating'],
            "comment": visit['comment'],
        })
    return result


def initialize_demo_data():
    user_check = db.query("MATCH (u:User) RETURN count(u) AS count")
    if user_check[0]['count'] > 0:
        return

    def create_coordinates(longitude: float, latitude: float):
        r = 0.0002
        coords = []
        for i in range(8):
            coords.append({
                "longitude": longitude + r * math.sin(i * math.pi / 4),
                "latitude": latitude + r * math.cos(i * math.pi / 4)
            })
        return coords

    print("Инициализация демонстрационных данных...")
    coord1 = create_coordinates(longitude=30.283151, latitude=59.916766)
    coord2 = create_coordinates(longitude=30.290646, latitude=59.953568)
    coord3 = create_coordinates(longitude=30.307252, latitude=59.963390)
    demo_data = {
        'users': [
            {
                "last_name": "Иванов",
                "first_name": "Иван",
                "patronymic": "Иванович",
                "nickname": "ivanov",
                "password": "$2b$12$XI2tINfrLsf5YWKoePOnTOZRGQ5jGp0K7Ciand3r9hTcmin5l4jLK",
                "avatar_url": "https://ui-avatars.com/api/?name=John+Doe"
            },
            {
                "last_name": "Петров",
                "first_name": "Петр",
                "patronymic": "Петрович",
                "nickname": "petrov",
                "password": "password",
                "avatar_url": "https://ui-avatars.com/api/?name=John+Doe"
            },
            {
                "last_name": "Сидоров",
                "first_name": "Николай",
                "patronymic": "Николаевич",
                "nickname": "sidorov",
                "password": "$2b$12$XI2tINfrLsf5YWKoePOnTOZRGQ5jGp0K7Ciand3r9hTcmin5l4jLK",  # password
                "avatar_url": "https://ui-avatars.com/api/?name=John+Doe"
            }
        ],
        'courtyards': [
            {
                "title": "Двор дома-утюга",
                "houses": ["наб. реки Фонтанки, д. 199", "Садовая ул., д. 128"],
                "coordinates": coord1
            },
            {
                "title": "Двор-восьмиугольник",
                "houses": ["Малый просп. П. С., д. 1б"],
                "coordinates": coord2
            },
            {
                "title": "Бармалеева, 4",
                "houses": ["Бармалеева, 4"],
                "coordinates": coord3
            }
        ],
        'visits': [
            {
                'username': 'ivanov',
                'courtyard_title': 'Двор дома-утюга',
                'visited_at': '2024-11-08',
                'rating': 5,
                'comment': 'Отличный двор!',
            },
            {
                'username': 'ivanov',
                'courtyard_title': 'Двор-восьмиугольник',
                'visited_at': "2024-11-09",
                'rating': 3,
                'comment': 'Двор так себе, видел и лучше.',
            },
            {
                'username': 'petrov',
                'courtyard_title': 'Двор-восьмиугольник',
                'visited_at': "2024-11-09",
                'rating': 4,
            },
            {
                'username': 'ivanov',
                'courtyard_title': 'Бармалеева, 4',
                'visited_at': "2024-11-11",
                'rating': 5,
                'comment': 'Крайне советую это место, было очень интересно здесь побывать'
            }
        ]
    }

    import_data(demo_data)


initialize_demo_data()
