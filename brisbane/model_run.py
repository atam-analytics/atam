import os
import sys
sys.path.append(os.path.join(os.getcwd(), '02_scripts'))
from model_functions import Model

def run_model(model_id, network_case, demand_case):
    # Create a model instance
    model = Model(model_id)
    model.zone_input_file = "zones.csv"
    model.network_case = network_case
    model.demand_case = demand_case
    print(model.attributes())

    # Network
    network = model.get_network()
    connectors = model.get_connectors()
    graph_df = model.build_network_graph(network, connectors)
    print(graph_df.head(-5))

    # Get demand matrix
    unit_demand_df = model.get_demand(model.demand_case)
    print(unit_demand_df.head(-5))

    # Assign demand to network
    model.assign_demand(unit_demand_df)

    """
    # Summarise outputs
    paths_file = os.path.join(model.run_output_dir, 'path_outputs.csv')
    links_outputs_df = model.output_link_results(paths_file) # link outputs
    matrix_df = model.output_cost_matrix(paths_file) # matrix outputs
    sla_paths_df = model.select_link_analysis(paths_file) # select link analysis

    # Run Accessibility Analysis
    model.analyse_accessibility()
    """

    
if __name__ == "__main__":
    model_id = sys.argv[1]
    network_case = sys.argv[2]
    demand_case = sys.argv[3]
    run_model(model_id, network_case, demand_case)