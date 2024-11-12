from neo4j import GraphDatabase, Result
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword")


class Database:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.tx = None
        self.session = None

    def close(self):
        if self.session:
            self.session.close()
        self.driver.close()

    def query(self, query, parameters=None):
        session_used = self.tx or self.session or self.driver.session()

        try:
            print("Запрос:", query)
            print("С параметрами:", parameters)

            result = session_used.run(query, parameters or {})
            results_data = [record.data() for record in result]

            print("Результат:", results_data)

            return results_data
        finally:
            if not self.tx and not self.session:  # Close only temporary session
                session_used.close()

    def begin(self):
        if self.session is None:
            self.session = self.driver.session()
        if self.tx is None:
            self.tx = self.session.begin_transaction()

    def commit(self):
        if self.tx:
            self.tx.commit()
            self.tx = None
        if self.session:
            self.session.close()
            self.session = None

    def rollback(self):
        if self.tx:
            self.tx.rollback()
            self.tx = None
        if self.session:
            self.session.close()
            self.session = None


db = Database(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
