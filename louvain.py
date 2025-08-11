from graphdatascience import GraphDataScience

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "and123$$"
DB = "neo4j"

gds = GraphDataScience(URI, auth=(USER,PASSWORD))

gds.set_database(DB)
print(gds.version())

