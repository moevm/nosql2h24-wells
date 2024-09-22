import os
from neo4j import GraphDatabase
import bcrypt
from datetime import datetime


def create_user(tx, email, name, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    query = """
    CREATE (u:User {email: $email, name: $name, password: $password})
    RETURN u
    """
    tx.run(query, email=email, name=name, password=hashed_password.decode('utf-8'))


def create_courtyard(tx, latitude, longitude, address, name, description=None):
    query = """
    CREATE (c:Courtyard {latitude: $latitude, longitude: $longitude, address: $address, name: $name, description: $description})
    RETURN c
    """
    tx.run(query, latitude=latitude, longitude=longitude, address=address, name=name, description=description)


def create_visit(tx, user_id, courtyard_id, date):
    query = """
    MATCH (u:User) WHERE ID(u)=$user_id
    MATCH (c:Courtyard) WHERE ID(c)=$courtyard_id
    CREATE (u)-[:VISIT {date: $date}]->(c)
    RETURN u, c
    """
    tx.run(query, user_id=user_id, courtyard_id=courtyard_id, date=date)


def get_users(tx):
    query = """
    MATCH (u:User)
    RETURN ID(u) AS id
    """
    result = tx.run(query)
    return [record["id"] for record in result]


def get_courtyards(tx):
    query = """
    MATCH (c:Courtyard)
    RETURN ID(c) AS id
    """
    result = tx.run(query)
    return [record["id"] for record in result]


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Создание пользователя
        session.execute_write(create_user, "user@example.com", "John Doe", "password123")

        users = session.execute_read(get_users)
        print("Users from DB:", users)

        # Создание двора
        session.execute_write(create_courtyard, 55.751244, 37.618423, "123 Main St", "Central Park", "A beautiful park")

        courtyards = session.execute_read(get_courtyards)
        print("Courtyards from DB:", courtyards)

        # Посещение
        session.execute_write(create_visit, users[-1], courtyards[-1], datetime.now().strftime("%Y-%m-%d"))

    driver.close()


if __name__ == "__main__":
    main()
