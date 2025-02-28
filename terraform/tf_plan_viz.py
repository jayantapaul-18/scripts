import json
import networkx as nx
import matplotlib.pyplot as plt

# Load the Terraform plan JSON
with open("tfplan.json", "r") as file:
    tfplan = json.load(file)

# Create a directed graph
graph = nx.DiGraph()

# Parse resource changes
for change in tfplan.get("resource_changes", []):
    resource_address = change["address"]
    action = change["change"]["actions"]
    actions_str = "".join(action)
    
    # Add node for the resource
    graph.add_node(resource_address, action=actions_str)
    
    # Add edges for dependencies
    for dep in change.get("change", {}).get("before", {}).get("dependencies", []):
        graph.add_edge(dep, resource_address)

# Draw the graph
pos = nx.spring_layout(graph, seed=42)
plt.figure(figsize=(12, 8))

# Color nodes based on actions
node_colors = []
for node in graph.nodes:
    action = graph.nodes[node].get("action", "")
    if action == "create":
        node_colors.append("green")
    elif action == "delete":
        node_colors.append("red")
    elif action == "update":
        node_colors.append("blue")
    else:
        node_colors.append("gray")

# Draw nodes and edges
nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=2000)
nx.draw_networkx_edges(graph, pos, arrowstyle="->", arrowsize=10)
nx.draw_networkx_labels(graph, pos, font_size=10, font_color="white")

# Add legend
legend_labels = {
    "Create": "green",
    "Delete": "red",
    "Update": "blue",
    "No Change": "gray"
}
for label, color in legend_labels.items():
    plt.scatter([], [], c=color, label=label)
plt.legend(scatterpoints=1, frameon=False, title="Actions")

# Show the graph
plt.title("Terraform Plan Visualization")
plt.show()