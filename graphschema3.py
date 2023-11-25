import time
from neo4j import GraphDatabase

# Function to establish a session with Neo4j
def neo4j_session(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver.session()

# Function to execute and fetch the query result
def execute_fetch_(query, session):
    print(query)
    result = session.run(query)
    return [record for record in result]

class GraphSchema():
    def __init__(self):
        self.queries = {}
        self.session = neo4j_session("bolt://n4j.brainchain.cloud", "neo4j", "password")
        self.edge_labels = self.get_edge_labels()
        self.schema_map = {}
        self.node_properties_map = {}
        self.relationship_properties_map = {}
        self.relationships_map = {}
        self.schema = self.graph_schema()

    def get_edge_labels(self):
        # Adjust this query to fit Neo4j syntax if necessary
        query = "MATCH ()-[r]->() RETURN DISTINCT type(r) as edge_label"
        results = execute_fetch_(query, self.session)
        return [result['edge_label'] for result in results]

    def graph_schema(self):
        for edge_label in self.edge_labels:
            query = f"""
            MATCH (a)-[r:{edge_label}]->(b)
            WITH a, r, b, rand() AS random
            ORDER BY random
            RETURN 
                labels(a) as source_labels,
                labels(b) as target_labels,
                keys(a) as source_properties,
                keys(b) as target_properties,
                keys(r) as relationship_properties
            LIMIT 100;
            """
            self.queries[edge_label] = query


        for edge_label in self.queries:
            query = self.queries[edge_label]
            results = execute_fetch_(query, self.session)
            # print(results)

            # Initialize a temporary schema for each edge_label
            temp_schema = {
                'source_labels': set(),
                'target_labels': set(),
                'source_properties': set(),
                'target_properties': set(),
                'relationship_properties': set()
            }

            for result in results:
                # For each result, add labels and properties to the temporary schema
                temp_schema['source_labels'].update(result['source_labels'])
                temp_schema['target_labels'].update(result['target_labels'])
                temp_schema['source_properties'].update(result['source_properties'])
                temp_schema['target_properties'].update(result['target_properties'])
                temp_schema['relationship_properties'].update(
                    result['relationship_properties'])

            # Convert sets to lists before adding to schema_map
            self.schema_map[edge_label] = {
                'source_labels': list(temp_schema['source_labels']),
                'target_labels': list(temp_schema['target_labels']),
                'source_properties': list(temp_schema['source_properties']),
                'target_properties': list(temp_schema['target_properties']),
                'relationship_properties': list(temp_schema['relationship_properties'])
            }

        # Extract node properties
        for rel, info in self.schema_map.items():
            for label in info["source_labels"]:
                if label not in self.node_properties_map:
                    self.node_properties_map[label] = set()
                for prop in info["source_properties"]:
                    self.node_properties_map[label].add(prop)
            for label in info["target_labels"]:
                if label not in self.node_properties_map:
                    self.node_properties_map[label] = set()
                for prop in info["target_properties"]:
                    self.node_properties_map[label].add(prop)

        node_properties_output = []
        for label, properties in self.node_properties_map.items():
            node_str = f"Node label: '{label}', '{label}' properties: "
            properties_list = [prop for prop in properties]
            node_properties_output.append(node_str + str(properties_list))

        # Extract relationship properties
        relationship_properties_output = []
        for rel, info in self.schema_map.items():
            if info["relationship_properties"]:
                rel_str = f"Relationship Name: '{rel}', Relationship Properties: "
                properties_list = [prop for prop in info["relationship_properties"]]
                relationship_properties_output.append(rel_str + str(properties_list))

        # Extract relationships
        relationships_output = []
        for rel, info in self.schema_map.items():
            for source in info["source_labels"]:
                for target in info["target_labels"]:
                    relationships_output.append(f"(:{source})-[:{rel}]->(:{target})")

        output = "Node properties are the following:\n"
        output += "\n".join(node_properties_output)
        output += "\nRelationship properties are the following:\n"
        output += "\n".join(relationship_properties_output)
        output += "\nThe relationships are the following:\n"
        output += "\n".join(relationships_output)
        
        time2 = time.time()
        return output
        # print(time2)
        # print("Entire operation took: ", time2-time1)
