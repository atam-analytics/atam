# Active Transport Analytics Model {ATAM}
# Import dependencies
import os
import sys
sys.path.append(os.path.join(os.getcwd(), '02_scripts'))
from model_functions import Model

# Create a model instance
model = Model('R0002')
model.network_input_file = "links.csv"
model.zone_input_file = "zones.csv"
model.connectors_input_file = "connectors.csv"
model.cycle_demand_input_file = "cycling_demand.csv"
print(model.attributes())

# Network
network = model.get_network()
connectors = model.get_connectors()
graph_df = model.build_network_graph(network, connectors)
print(graph_df.head(-5))

# Get demand matrix
cycle_demand_df = model.get_demand(model.cycle_demand_input_file)
print(cycle_demand_df.head(-5))

# Assign demand to network
model.assign_demand(cycle_demand_df)

# Run Accessibility Analysis
model.analyse_accessibility()

# Summarise outputs
paths_file = os.path.join(model.run_output_dir, 'path_outputs.csv')
links_outputs_df = model.output_link_results(paths_file) # link outputs
matrix_df = model.output_cost_matrix(paths_file) # matrix outputs
sla_paths_df = model.select_link_analysis(paths_file) # select link analysis