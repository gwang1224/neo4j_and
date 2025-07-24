from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
import json

class Neo4jImportData:

    def __init__(self, uri, user, password, db, data_path):
        """
        Args
            uri (str): neo4j uri
            user (str): instance username
            password (str): instance password
            db (str): database name
            data_path (str): OpenAlex data in json format... see cache and neo4j_data.py
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user,password))
            self.driver.verify_connectivity()
            print("Connection to Neo4j database successful!")
        except ServiceUnavailable as e:
            print(f"Connection failed: {e}")

        self.db = db

        with open(data_path,'r') as file:
            self.data = json.load(file)

    def close(self):
        self.driver.close()

    
    def publication_as_nodes(self):
        """
        Adds each publication as a node with metadata id, title, year, authors
        """
        for work in self.data['works_data']:
            id, title, year, authors, venue = (
                self.data['works_data'][work][k] for k in ['id', 'title', 'year', 'authors', 'venue']
            )

            # Must convert authors data to json string
            author_string = json.dumps(authors)

            try:
                summary = self.driver.execute_query("""
                    CREATE (n:PUBLICATION {id: $pub_id, title: $pub_title, year: $pub_year, authors: $pub_authors, venue: $pub_venue})
                    """,
                    pub_id = id, pub_title = title, pub_year = year, pub_authors = author_string, pub_venue = venue,
                    database = self.db,
                ).summary
                print("Added {nodes_created} nodes in {time} ms.".format(
                    nodes_created = summary.counters.nodes_created,
                    time = summary.result_available_after
                ))

            except KeyError as ke:
                print(f"Missing key in work data: {ke}")
            except Neo4jError as ne:
                print(f"Neo4j error while inserting '{title}': {ne}")
            except Exception as e:
                print(f"Unexpected error: {e}")

        print("All nodes were successfully added.")


    def node_count(self):
        """
        Counts nodes 
        """
        result = self.driver.execute_query("""
            MATCH (n) RETURN count(n) AS node_count
        """,
        database = self.db)
        count = result.records[0]["node_count"]
        print(f"Number of nodes: {count}")


    def delete_all_nodes(self):
        """
        Deletes all nodes
        """
        self.driver.execute_query("""
            MATCH (n) DETACH DELETE n
        """,
        database = self.db)
        print("All nodes were successfully deleted.")
        self.node_count()


if __name__ == "__main__":

    URI = "neo4j://127.0.0.1:7687"
    USER = "neo4j"
    PASSWORD = "and123$$"
    DB = "neo4j"
    PATH = "/Users/gracewang/Documents/UROP_Summer_2025/neo4j_and/cache/Russell Bowler_data.json"

    imp = Neo4jImportData(URI, USER, PASSWORD, DB, PATH)
    imp.delete_all_nodes()
    imp.publication_as_nodes()
    imp.node_count()
    imp.delete_all_nodes()
    imp.close()