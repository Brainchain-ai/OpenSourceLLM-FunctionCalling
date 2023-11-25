import concurrent.futures
import graphviz
import re
from collections import defaultdict
import uuid

class Node:
    def __init__(self, step):
        self.step = step
        self.dependencies = set()
        self.dependents = set()

class DependencyGraph:
    def __init__(self, plan):
        print("Type plan: ", type(plan), "\nPlan: ", plan)
        if type(plan) == list:
            plan = plan[-1]

        if type(plan) != dict:
            plan = plan.dict()

        if 'plan' in plan:
            self.plan = plan
            self.nodes = {step['plan_step_index']: Node(step) for step in plan['plan']}
            self.populate_dependencies(plan)
            self.post_process_dependencies()
        else:
            raise ValueError("Invalid plan passed to DependencyGraph: {} - missing 'plan' key. Steps must each have 'plan_step_index', 'dependencies', and 'step' keys.".format(plan))
    def analyze_textual_dependencies(self):
        """
        Analyze the textual content of each step to infer possible dependencies.
        """
        for index, node in self.nodes.items():
            for other_index, other_node in self.nodes.items():
                if index != other_index:
                    if self.has_textual_dependency(node.step["step"], other_node.step["step"]):
                        node.dependencies.add(self.nodes[other_index])
                        self.nodes[other_index].dependents.add(node)

    @staticmethod
    def has_textual_dependency(step_text, other_step_text):
        """
        Check if 'step_text' has a dependency on 'other_step_text' based on textual content.
        """
        # This is a simple example where we check if the other step's text is referenced in the current step's text.
        # More advanced NLP techniques can be applied here for better accuracy.
        step_words = set(re.findall(r'\w+', step_text.lower()))
        other_step_words = set(re.findall(r'\w+', other_step_text.lower()))
        
        # Checking if the current step contains more than half of the words of the other step. 
        # This threshold can be adjusted.
        if len(step_words.intersection(other_step_words)) > len(other_step_words) / 2:
            return True
        return False

    def post_process_dependencies(self):
        pass
        # self.analyze_textual_dependencies()

    def populate_dependencies(self, plan):
        for step in plan['plan']:
            index = step['plan_step_index']
            for dep_index in step['dependencies']:
                self.nodes[index].dependencies.add(self.nodes[dep_index])
                self.nodes[dep_index].dependents.add(self.nodes[index])

    def visualize(self, filename=None):
        dot = graphviz.Digraph(format='png', engine='dot')
        
        with dot.subgraph() as main:
            for index, node in self.nodes.items():
                main.node(str(index))
                for dep in node.dependencies:
                    main.edge(str(dep.step['plan_step_index']), str(index))
        
        # Create a legend as a table
        legend_table = '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
            <TR><TD>Index</TD><TD>Step</TD><TD>Num Dependencies</TD></TR>'''  # Added new header for Num Dependencies

        for index, node in self.nodes.items():
            num_dependencies = len(node.dependencies)  # Count the number of dependencies
            legend_table += f'<TR><TD>{index}</TD><TD>{node.step["step"]}</TD><TD>{num_dependencies}</TD></TR>'  # Added new column

        legend_table += '</TABLE>>'

        dot.node('legend', label=legend_table, shape='plaintext')

        dot.attr(overlap='false', rankdir='LR')  # Layout from left to right
        
        random_file_name = filename or f"{uuid.uuid4()}"  # Generate a random file name using uuid
        print(f"Saving dependency graph to {random_file_name}.png")
        dot.render(random_file_name, view=True)  # This will create a PNG image and open it

    def execute_step(self, step):
        # Implement the actual logic to execute the step
        # ...
        pass

    def execute_plan(self):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Initially, find all tasks with no dependencies
            no_dependencies = [node for node in self.nodes.values() if not node.dependencies]
            while no_dependencies:
                futures = {executor.submit(self.execute_step, node.step): node for node in no_dependencies}
                for future in concurrent.futures.as_completed(futures):
                    node = futures[future]
                    # Remove completed node from dependencies of other nodes
                    for dependent in node.dependents:
                        dependent.dependencies.remove(node)
                        if not dependent.dependencies:
                            no_dependencies.append(dependent)
                    no_dependencies.remove(node)

# Usage
# plan = {'plan': [{'plan_step_index': 0, 'dependencies': [], 'step': 'Use the web_search tool to find the current weather in SF.'}, {'plan_step_index': 1, 'dependencies': [], 'step': 'Use the web_search tool to find the current weather in LA.'}, {'plan_step_index': 2, 'dependencies': [], 'step': 'Use the web_search tool to find the current weather in Washington DC.'}, {'plan_step_index': 3, 'dependencies': [], 'step': 'Use the web_search tool to find the current weather in Miami.'}, {'plan_step_index': 4, 'dependencies': [0, 1, 2, 3], 'step': 'Compare and contrast the weather in SF and LA.'}, {'plan_step_index': 5, 'dependencies': [0, 1, 2, 3], 'step': 'Compare and contrast the weather in Washington DC and Miami.'}, {'plan_step_index': 6, 'dependencies': [4, 5], 'step': 'Compare and contrast the weather in SF and LA with Washington DC and Miami.'}, {'plan_step_index': 7, 'dependencies': [0, 1, 2, 3], 'step': 'Create a Markdown table with all four cities, and four columns with temperature, wind speed, humidity, and highs and lows of the day, for today.'}]}

# dependency_graph = DependencyGraph(plan)
# dependency_graph.visualize()  # This will create a PNG image and open it
# dependency_graph.execute_plan()
