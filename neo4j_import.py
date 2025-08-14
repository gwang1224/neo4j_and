"""
Neo4j import script (step 2 of 2)

Purpose
- Read the cached JSON produced by `neo4j_data.py`
- Create publication nodes and similarity edges in Neo4j for disambiguation experiments

Current capabilities
- PUBLICATION nodes with properties: id, title, year, authors (JSON string), venue
- COAUTHOR edges: connect publications that share at least one author
- COVENUE edges: connect publications that share the same venue
- COTITLE edges: connect publications with similar

Usage
1) Ensure a Neo4j instance is running and accessible
2) Set connection variables in the main block (URI, USER, PASSWORD, DB, PATH)
3) Run from repo root, e.g. `PYTHONPATH=. python neo4j_import.py`

Outputs (example counts from "David Nathan")
- 413 nodes
- 22,953 relationships total
- 5,113 COVENUE relationships
- 17,840 COAUTHOR relationships

Notes
- Relationships are currently modeled as directional in code, but clustering can treat the graph as undirected
- Consider converting to undirected by creating a single relationship with `MERGE` or by normalizing during analysis
"""

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
import json
from typing import List, Dict, Tuple

# For CoTitle similarity
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as _e:  # pragma: no cover - optional at import time
    TfidfVectorizer = None
    cosine_similarity = None

class Neo4jImportData:

    def __init__(self, uri, user, password, db, data_path):
        """
        Initialize a Neo4j driver and load the cached data

        Args
            uri (str): Neo4j URI (e.g. bolt://localhost:7687)
            user (str): instance username
            password (str): instance password
            db (str): database name
            data_path (str): Path to JSON created by neo4j_data.py (cache/<Author>_data.json)
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user,password))
            self.driver.verify_connectivity()
            print("Connection to Neo4j database successful!")
        except ServiceUnavailable as e:
            print(f"Connection failed: {e}")

        self.db = db

        with open(data_path,'r', encoding='utf-8') as file:
            self.data = json.load(file)

    def close(self):
        self.driver.close()

    
    def publication_as_nodes(self):
        """
        Create PUBLICATION nodes with properties id, title, year, authors (JSON string), venue
        """
        for work in self.data['works_data']:
            pub_id, title, year, authors, venue = (
                self.data['works_data'][work][k] for k in ['id', 'title', 'year', 'authors', 'venue']
            )

            # Must convert authors data to json string
            author_string = json.dumps(authors)

            try:
                summary = self.driver.execute_query("""
                    CREATE (n:PUBLICATION {id: $pub_id, title: $pub_title, year: $pub_year, authors: $pub_authors, venue: $pub_venue})
                    """,
                    pub_id = pub_id, 
                    pub_title = title, 
                    pub_year = year, 
                    pub_authors = author_string, 
                    pub_venue = venue,
                    database = self.db,
                )

            except KeyError as ke:
                print(f"Missing key in work data: {ke}")
            except Neo4jError as ne:
                print(f"Neo4j error while inserting '{title}': {ne}")
            except Exception as e:  # Keep broad catch to continue bulk ingestion
                print(f"Unexpected error creating PUBLICATION node: {e}")

        print("All nodes were successfully added.")


    def node_count(self):
        """
        Print total node count
        """
        result = self.driver.execute_query("""
            MATCH (n) RETURN count(n) AS node_count
        """,
        database = self.db)
        count = result.records[0]["node_count"]
        print(f"Number of nodes: {count}")

    def edge_count(self):
        """
        Print total relationship count
        """
        result = self.driver.execute_query(
            """
            MATCH ()-[r]->() RETURN COUNT(r) AS totalRelationships
            """,
            database=self.db
        )
        count = result.records[0]["totalRelationships"]
        print(f"Total relationships: {count}")


    def delete_all_nodes(self):
        """
        Delete all nodes and relationships from the selected database
        """
        self.driver.execute_query("""
            MATCH (n) DETACH DELETE n
        """,
        database = self.db)
        print("All nodes were successfully deleted.")
        self.node_count()


    def add_covenue_edge(self):
        """
        Create COVENUE edges between publications that share the same venue
        Currently directional; community detection can treat as undirected
        """
        id_venue = {}
        for work_data in self.data['works_data'].values():
            pub_id = work_data['id']
            venue = work_data['venue']
            id_venue[pub_id] = venue

        created_edges = 0

        pub_keys = list(id_venue.keys())
        for i, pub1 in enumerate(pub_keys):
            for pub2 in pub_keys[i+1:]:
                if id_venue[pub1] == id_venue[pub2]:
                    #print(f"Trying edge between {pub1} and {pub2}, venue: {id_venue[pub1]}")
                    self.driver.execute_query("""
                        MATCH (p1:PUBLICATION {id: $pub_name1}), (p2:PUBLICATION {id: $pub_name2})
                        CREATE (p1) - [:COVENUE {venue: $pub_venue}] -> (p2)
                    """,
                    pub_name1 = pub1, 
                    pub_name2 = pub2, 
                    pub_venue = id_venue[pub1],
                    database = self.db
                    )
                    created_edges += 1
        
        print(f" Created {created_edges} CoVenue relationships.")


    def add_coauthor_edge(self):
        """
        Create COAUTHOR edges between publications that share at least one author
        Adds a `weight` equal to the number of shared authors
        Currently directional; community detection can treat as undirected
        """

        works_data = self.data['works_data']

        #print(works_data)
        created_edges = 0

        pub_keys = list(works_data.keys())
        # Creates a set of pub1 authors
        for i, pub1 in enumerate(pub_keys):
            authors1 = works_data[pub1]['authors']
            set1 = {(a['id'], a['name']) for a in authors1}

            # Set of pub2 authors
            for pub2 in pub_keys[i+1:]:
                authors2 = works_data[pub2]['authors']
                set2 = {(a['id'], a['name']) for a in authors2}

                # Shared authors between two publications, including ambiguous name
                shared_authors = set1 & set2

                #### FUTURE: may need to create metric for number of shared authors for weighted edge
                if shared_authors:
                    shared_authors_json = [{"id": aid, "name": name} for (aid, name) in shared_authors]
                    json_string = json.dumps(shared_authors_json)

                    # Add weight for COAUTHOR (# of shared authors)
                    weight = len(shared_authors)

                    self.driver.execute_query(
                        """
                        MATCH (p1:PUBLICATION {id: $pub_name1}), (p2:PUBLICATION {id: $pub_name2})
                        CREATE (p1)-[:COAUTHOR {coauthor: $pub_coauthor, weight: $weight}]->(p2)
                        """,
                        pub_name1=pub1,
                        pub_name2=pub2,
                        pub_coauthor=json_string,
                        weight = weight,
                        database=self.db
                    )
                    created_edges += 1
                    #print(f" Created {created_edges} relationships.")
            
        print(f" Created {created_edges} CoAuthor relationships.")

    def cotitle_pairs_tfidf(self, min_similarity=0.60, max_features=10000):
        """
        Create COTITLE pairs using TF-IDF cosine similarity between publication titles.

        Args
            min_similarity: minimum cosine similarity to create an edge
            top_k: for each publication, create edges only to its top_k most similar publications

        Requirements
            scikit-learn must be installed (see requirements.txt)
        """
        works_data = self.data["works_data"]
        pub_ids = list(works_data.keys())
        titles = [works_data[pid].get("title") or "" for pid in pub_ids]

        vec = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=max_features
        )
        X = vec.fit_transform(titles)

        # sparse cosine sim
        S = cosine_similarity(X, dense_output=False).tocsr()

        pairs = []
        # iterate upper triangle only (undirected)
        S_coo = S.tocoo()
        for i, j, sim in zip(S_coo.row, S_coo.col, S_coo.data):
            if i < j and sim >= min_similarity:
                pairs.append((pub_ids[i], pub_ids[j], float(sim)))
        return pairs

    def add_cotitle_edge_from_pairs(self, pairs, threshold=0.60):
        created = 0
        for id1, id2, sim in pairs:
            if id1 == id2 or sim < threshold:
                continue
            a, b = (id1, id2) if id1 < id2 else (id2, id1)
            self.driver.execute_query(
                """
                MATCH (p1:PUBLICATION {id: $a}), (p2:PUBLICATION {id: $b})
                MERGE (p1)-[r:COTITLE]->(p2)
                SET r.similarity = $sim
                """,
                a=a, b=b, sim=float(sim), database=self.db
            )
            created += 1
        print(f"Created {created} COTITLE edges (cosine ≥ {threshold}).")


if __name__ == "__main__":

    URI = "neo4j://127.0.0.1:7687"
    USER = "neo4j"
    PASSWORD = "and123$$"
    DB = "neo4j"
    PATH = "/Users/gracewang/Documents/UROP_Summer_2025/neo4j_and/cache/David Nathan_data.json"

    imp = Neo4jImportData(URI, USER, PASSWORD, DB, PATH)

    imp.delete_all_nodes()

    # Add all publications
    imp.publication_as_nodes()

    # Add covenue, coauthor, cotitle
    imp.add_covenue_edge()
    imp.add_coauthor_edge()

    pairs = imp.cotitle_pairs_tfidf()
    imp.add_cotitle_edge_from_pairs(pairs)

    # Metrics
    imp.node_count()
    imp.edge_count()
