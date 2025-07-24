from neo4j import GraphDatabase


# Importing data into Neo4j, ref: https://neo4j.com/docs/python-manual/current/
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "and123$$")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()

summary = driver.execute_query("""
    CREATE (a:Person {name: $name})
    CREATE (b:Person {name: $friendName})
    CREATE (a) - [:LIKES] -> (b)                          
    """,
    name = "Grace", friendName="Leo",
    database_="neo4j",
).summary
print("Created {nodes_created} nodes in {time} ms.".format(
    nodes_created=summary.counters.nodes_created,
    time=summary.result_available_after
))

