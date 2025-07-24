from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import json


# Importing data into Neo4j, ref: https://neo4j.com/docs/python-manual/current/
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "and123$$")

try:
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection to Neo4j database successful!")
except ServiceUnavailable as e:
    print(f"Connection failed: {e}")


def publication_as_nodes(driver, json_path):
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

        driver.execute_query("""
            CREATE (n:PUBLICATION {id: $pub_id, title: $pub_title, year: $pub_year})
            """,
            pub_id = id, pub_title = title, pub_year = year,
            database = "neo4j",
        )
    

publication_as_nodes(driver, "/Users/gracewang/Documents/UROP_Summer_2025/neo4j_and/cache/Russell Bowler_data.json")

#def delete_all_nodes(driver):

# summary = driver.execute_query("""
#     CREATE (a:Person {name: $name})
#     CREATE (b:Person {name: $friendName})
#     CREATE (a) - [:LIKES] -> (b)                          
#     """,
#     name = "Grace", friendName="Leo",
#     database_="neo4j",
# ).summary
# print("Created {nodes_created} nodes in {time} ms.".format(
#     nodes_created=summary.counters.nodes_created,
#     time=summary.result_available_after
# ))
