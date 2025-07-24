from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
import json

# Importing data into Neo4j, ref: https://neo4j.com/docs/python-manual/current/
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "and123$$")

# Replace with the name of your database
database_name = "neo4j"

try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    print("Connection to Neo4j database successful!")
except ServiceUnavailable as e:
    print(f"Connection failed: {e}")


def publication_as_nodes(driver, json_path, db):
    """
    Adds each publication as a node with metadata id, title, year, authors

    Args
        driver (Object): neo4j
        json_path (str): OpenAlex data... see cache
    """
    with open(json_path,'r') as file:
        data = json.load(file)

    for work in data['works_data']:
        id, title, year, authors = (
            data['works_data'][work][k] for k in ['id', 'title', 'year', 'authors']
        )
        try:
            summary = driver.execute_query("""
                CREATE (n:PUBLICATION {id: $pub_id, title: $pub_title, year: $pub_year})
                """,
                pub_id = id, pub_title = title, pub_year = year,
                database = db,
            ).summary
            print("Added {nodes_created} nodes in {time} ms.".format(
                nodes_created = summary.counters.nodes_created,
                time = summary.result_available_after
            ))

            print("All nodes were successfully added.")

        except KeyError as ke:
            print(f"Missing key in work data: {ke}")
        except Neo4jError as ne:
            print(f"Neo4j error while inserting '{title}': {ne}")
        except Exception as e:
            print(f"Unexpected error: {e}")


def node_count(driver, db):
    """
    Counts nodes 
    """
    result = driver.execute_query("""
        MATCH (n) RETURN count(n) AS node_count
    """,
    database=db)
    count = result.records[0]["node_count"]
    print(f"Number of nodes: {count}")


def delete_all_nodes(driver, db):
    """
    Deletes all nodes
    """
    driver.execute_query("""
        MATCH (n) DETACH DELETE n
    """,
    database = db)
    print("All nodes were successfully deleted.")
    node_count(driver, db)


if __name__ == "__main__":
    # Testing using Russel Bowler data
    publication_as_nodes(driver, "/Users/gracewang/Documents/UROP_Summer_2025/neo4j_and/cache/Russell Bowler_data.json", database_name)
    node_count(driver, database_name)
    delete_all_nodes(driver, database_name)
    driver.close()
