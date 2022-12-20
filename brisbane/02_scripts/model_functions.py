# Dependencies
import os
import pandas as pd
import numpy as np
import csv
import networkx as nx

# Model class
class Model:
    "Model class"
    
    # Init
    def __init__(self, run_name):
        # Name
        self.run_name = run_name
        
        # Input files (set as placeholders)
        self.network_input_file = "" 
        self.zone_input_file = "" 
        self.connectors_input_file = "" 
        self.walk_demand_input_file = "" 
        self.cycle_demand_input_file = "" 
        
        # Directory structure
        self.base_dir = os.getcwd()
        self.input_dir = os.path.join(self.base_dir, '01_inputs')
        self.scripts_dir = os.path.join(self.base_dir, '02_scripts')
        self.output_dir = os.path.join(self.base_dir, '03_outputs')       
        self.run_output_dir = self.safe_create_directory(os.path.join(self.output_dir, run_name))


    # Print self info
    def attributes(self):
        print("Run name:", self.run_name)
        print("Base directory:", self.base_dir)
        print("Inputs directory:", self.input_dir)
        print("Outputs directory:", self.output_dir)
        print("Run Outputs directory:", self.run_output_dir)
        print("Network Inputs:", self.network_input_file)
        print("Connectors Inputs:", self.connectors_input_file)
        print("Cycle Demand Inputs:", self.cycle_demand_input_file)
        print("Walk Demand Inputs:", self.walk_demand_input_file)

        
    # Create directory
    def safe_create_directory(self, dir_path):
        isExist = os.path.exists(dir_path)
        if not isExist:  
          # Create a new directory because it does not exist 
          os.makedirs(dir_path)
          print("New directory created: ", dir_path)
        return dir_path


    # Get Network as a pandas DataFrame
    def get_network(self):
    
        # Prescribed direction links
        self.network_input_fp = os.path.join(self.input_dir, '02_network', self.network_input_file)
        print("Network input file:", self.network_input_fp)
        self.network_inputs_df = pd.read_csv(self.network_input_fp)
        self.network_columns = self.network_inputs_df.columns.tolist()
        print("Network columns: ", self.network_columns)

        # Create links in opposite direction
        self.opposite_direction_df = pd.read_csv(self.network_input_fp)
        self.opposite_direction_df.rename(columns={
            "i_node": "j_node",
            "i_node_x": "j_node_x",
            "i_node_y": "j_node_y",
            "j_node": "i_node",
            "j_node_x": "i_node_x",
            "j_node_y": "i_node_y",
        }, inplace=True)
        self.opposite_direction_df = self.opposite_direction_df[self.network_columns]
        self.full_network_df = pd.concat([self.opposite_direction_df, self.network_inputs_df])
        return self.full_network_df     


    # Get Centroid Connectors as a pandas DataFrame
    def get_connectors(self):
    
        # Prescribed direction connectors
        self.connectors_input_fp = os.path.join(self.input_dir, '03_connectors', self.connectors_input_file)
        print("Connectors input file:", self.connectors_input_fp)
        self.connectors_input_df = pd.read_csv(self.connectors_input_fp)
        
        self.connectors_input_df.rename(columns={
            "zone_id": "i_node",
            "zone_x": "i_node_x",
            "zone_y": "i_node_y",
            "node_id": "j_node",
            "node_x": "j_node_x",
            "node_y": "j_node_y",
        }, inplace=True)
        
        self.connector_columns = self.connectors_input_df.columns.tolist()
        print("Connector (renamed) columns: ", self.connector_columns)
        
        # Opposite direction connectors
        self.opposite_direction_connectors_df = pd.read_csv(self.connectors_input_fp)

        self.opposite_direction_connectors_df.rename(columns={
            "zone_id": "j_node",
            "zone_x": "j_node_x",
            "zone_y": "j_node_y",
            "node_id": "i_node",
            "node_x": "i_node_x",
            "node_y": "i_node_y"
        }, inplace=True)
        
        self.opposite_direction_connectors_df = self.opposite_direction_connectors_df[self.connector_columns]
        self.full_connectors_df = pd.concat([self.opposite_direction_connectors_df, self.connectors_input_df])     
        return self.full_connectors_df

        
    # Build network graph 
    def build_network_graph(self, network_df, connectors_df):
        # Concat network_df and connectors_df
        network_df['edge_type'] = "network"
        connectors_df['edge_type'] = "connector"
        self.graph_network_df = pd.concat([network_df, connectors_df])
        self.graph_network_df = self.graph_network_df[['i_node', 'j_node', 'cost_minutes', 'length_metres', 'edge_type','WKT']]
        
        # Export graph to CSV
        graph_csv_fp = os.path.join(self.run_output_dir, 'network_graph.csv')
        self.graph_network_df.to_csv(graph_csv_fp, index=False) 
        print("Exported network graph to ", graph_csv_fp)
        
        # Greate graph
        self.G = nx.from_pandas_edgelist(
            self.graph_network_df, 
            source='i_node', 
            target='j_node', 
            edge_attr=['cost_minutes'],
            create_using=nx.DiGraph 
        )
        
        return self.graph_network_df 


    # Get demand as a pandas DataFrame
    def get_demand(self, demand_input_fp):
        self.demand_input_fp = os.path.join(self.input_dir, '04_demand', demand_input_fp)
        print("Demand input file:", self.demand_input_fp)
        self.demand_df = pd.read_csv(self.demand_input_fp)
        self.demand_columns = self.demand_df.columns.tolist()
        print("Demand columns: ", self.demand_columns)
        return self.demand_df 
        
        
    # Assign demand to network
    def get_path(self, origin_zone, dest_zone, demand, cost_attribute):
        
        # Get path
        node_path = nx.dijkstra_path(self.G, origin_zone, dest_zone, cost_attribute)
        
        # Post-process results into df
        df = pd.DataFrame()
        df['i_node'] = node_path[:-1]
        df['j_node'] = node_path[1:]
        df['origin_zone'] = origin_zone
        df['dest_zone'] = dest_zone
        df['demand'] = demand
        df['segment_num'] = np.arange(df.shape[0])
        df['segment_num'] = df['segment_num']+1
        
        #Join all network attributes to the results df
        self.last_path_output_df = pd.merge(
            df, 
            self.graph_network_df, 
            how='inner', 
            left_on=['i_node', 'j_node'], 
            right_on = ['i_node', 'j_node']
        )
        
        return self.last_path_output_df


    # Assign demand matrix
    def assign_demand(self, demand_df):
        
        self.path_outputs_df = pd.DataFrame()
        print("Assigning demand...")
        
        for index, row in demand_df.iterrows():
            origin_zone = row['origin_zone']
            dest_zone = row['dest_zone']
            demand = row['demand']
            cost_attribute='cost_minutes'
            #print(index, ": orig=", origin_zone, ", dest=", dest_zone, ", demand=",demand)
            try:
                self.get_path(origin_zone, dest_zone, demand, cost_attribute)
                self.path_outputs_df = pd.concat([self.path_outputs_df, self.last_path_output_df])
            except:
                print("    An error occurred skimming origin {}, destination {}".format(origin_zone, dest_zone))
        
        # Format output
        self.path_outputs_df['od_pair'] = self.path_outputs_df['origin_zone'].astype(str) + "_" + self.path_outputs_df['dest_zone'].astype(str)
        
        # Export dataframe to CSV
        path_output_csv_fp = os.path.join(self.run_output_dir, 'path_outputs.csv')
        self.path_outputs_df.to_csv(path_output_csv_fp, index=False) 
        print("Assignment complete. Exported paths to ", path_output_csv_fp)
        
        return self.path_outputs_df
        
    
    # Process link volume outputs from path file
    def output_link_results(self, paths_file):
        
        # Summarise paths to links and sum demand
        path_df = pd.read_csv(paths_file)
        self.links_df = path_df.groupby(['i_node', 'j_node', 'length_metres', 'WKT']).sum('demand')
        self.links_df.reset_index(inplace=True)
        self.links_df['person_km'] = self.links_df['demand'] * (self.links_df['length_metres'].astype(float)/1000)
        self.links_df = self.links_df[['i_node', 'j_node', 'length_metres', 'WKT', 'demand', 'person_km']]
        
        # Export dataframe to CSV
        self.link_output_csv_fp = os.path.join(self.run_output_dir, 'link_outputs.csv')
        self.links_df.to_csv(self.link_output_csv_fp, index=False) 
        print("Exported link volumes to ", self.link_output_csv_fp)
        
        return self.links_df
        
    
    # Process cost matrix output from path file
    def output_cost_matrix(self, paths_file):
        
        path_df = pd.read_csv(paths_file)
        self.matrix_df = path_df.groupby(['od_pair','origin_zone', 'dest_zone']).agg({'demand':'mean', 'length_metres':'sum'})
        self.matrix_df.reset_index(inplace=True)        
        self.matrix_df = self.matrix_df[['origin_zone', 'dest_zone','demand','length_metres']]
        
        # Export dataframe to CSV
        self.matrix_output_csv_fp = os.path.join(self.run_output_dir, 'matrix_outputs.csv')
        self.matrix_df.to_csv(self.matrix_output_csv_fp, index=False) 
        print("Exported matrix output to ", self.matrix_output_csv_fp)
        
        return self.matrix_df


    # Process Select Link Analysis ("SLA") output from path file
    def run_select_link_analysis(self, paths_file, i_node, j_node, location_desc):

        self.sla_output_dir = self.safe_create_directory(os.path.join(self.run_output_dir, 'select_link_analysis'))
        
        path_df = pd.read_csv(paths_file)
        ij_string = str(i_node)+"_"+str(j_node)
        
        # Filter paths to where i_node and j_node are the selected link
        paths_step1_df = path_df[path_df['i_node']==i_node]
        paths_step2_df = paths_step1_df[paths_step1_df['j_node']==j_node]
        
        # Get list of origin_zone and dest_zone for those paths
        self.sla_od_pairs_df = paths_step2_df.groupby(['origin_zone', 'dest_zone']).sum()
        self.sla_od_pairs_df.reset_index(inplace=True)
        self.sla_od_pairs_df = self.sla_od_pairs_df[['origin_zone', 'dest_zone']] 
        self.sla_od_pairs_df['location_desc'] = location_desc      
        # Export Path Detailed Outputs
        self.sla_od_pairs_csv_fp = os.path.join(self.sla_output_dir, 'sla_{}_od_pairs.csv'.format(ij_string))
        self.sla_od_pairs_df.to_csv(self.sla_od_pairs_csv_fp, index=False) 
        print("Exported SLA OD Pairs to ", self.sla_od_pairs_csv_fp)
        
        # Get full paths for SLA OD pairs
        self.sla_paths_df = pd.merge(
            path_df, # Path outputs df 
            self.sla_od_pairs_df, # dataframe with OD pairs using selected link
            how='inner', 
            left_on=['origin_zone', 'dest_zone'], 
            right_on = ['origin_zone', 'dest_zone']
        )      
        # Export Path Detailed Outputs
        self.sla_paths_csv_fp = os.path.join(self.sla_output_dir, 'sla_{}_path_outputs.csv'.format(ij_string))
        self.sla_paths_df.to_csv(self.sla_paths_csv_fp, index=False) 
        print("Exported SLA paths to ", self.sla_paths_csv_fp)
            
        # Summarise SLA paths to links and sum demand
        self.sla_links_df = self.sla_paths_df.groupby(['location_desc','i_node', 'j_node', 'length_metres', 'WKT']).sum('demand')
        self.sla_links_df.reset_index(inplace=True)
        self.sla_links_df['person_km'] = self.sla_links_df['demand'] * (self.sla_links_df['length_metres'].astype(float)/1000)
        self.sla_links_df = self.sla_links_df[['location_desc','i_node', 'j_node', 'length_metres', 'WKT', 'demand', 'person_km']]
        
        # Export dataframe to CSV
        self.sla_link_output_csv_fp = os.path.join(self.sla_output_dir, 'sla_{}_link_outputs.csv'.format(ij_string))
        self.sla_links_df.to_csv(self.sla_link_output_csv_fp, index=False) 
        print("Exported SLA link volumes to ", self.sla_link_output_csv_fp)
        
        return self.sla_od_pairs_df, self.sla_paths_df, self.sla_links_df


    # Run a batch of select link analyses
    def select_link_analysis(self, paths_file):
        
        self.sla_input_file = os.path.join(self.input_dir, '05_analysis', 'sla_links.csv')
        sla_input_df = pd.read_csv(self.sla_input_file)
        
        self.all_sla_od_pairs_df = pd.DataFrame()
        self.all_sla_paths_df = pd.DataFrame()
        self.all_sla_links_df = pd.DataFrame()
        
        for index, row in sla_input_df.iterrows():
            i_node = row['i_node']
            j_node = row['j_node']
            location_desc = row['location_desc']
            paths_file = paths_file
            print(index, ": i_node=", i_node, ", j_node=", j_node, ", location_desc=",location_desc)
            try:
                self.sla_od_pairs_df, self.sla_paths_df, self.sla_links_df = self.run_select_link_analysis(paths_file, i_node, j_node, location_desc)
                self.all_sla_od_pairs_df = pd.concat([self.sla_od_pairs_df, self.all_sla_od_pairs_df])
                self.all_sla_paths_df = pd.concat([self.sla_paths_df, self.all_sla_paths_df])
                self.all_sla_links_df = pd.concat([self.sla_links_df, self.all_sla_links_df])
            except:
                print("    An error occurred: {}".format(Exception))
        
        # Export dataframes to CSV
        all_sla_od_pairs_fp = os.path.join(self.run_output_dir, 'sla_od_pairs.csv')
        self.all_sla_od_pairs_df.to_csv(all_sla_od_pairs_fp, index=False)        
        all_sla_paths_fp = os.path.join(self.run_output_dir, 'sla_paths.csv')
        self.all_sla_paths_df.to_csv(all_sla_paths_fp, index=False)        
        all_sla_links_fp = os.path.join(self.run_output_dir, 'sla_links.csv')
        self.all_sla_links_df.to_csv(all_sla_links_fp, index=False)      
        return self.all_sla_paths_df

    
    # Run accessibility analysis
    def analyse_accessibility(self):
    
        # Zones to analyse accessibility for
        self.accessibility_zones_file = os.path.join(self.input_dir, '05_analysis', 'accessibility_analysis_zones.csv')
        accessibility_zones_df = pd.read_csv(self.accessibility_zones_file)
        
        # All zones
        zones_fp = os.path.join(self.input_dir, '01_zones', self.zone_input_file)
        zones_df = pd.read_csv(zones_fp)
        
        self.path_outputs_df = pd.DataFrame()
        
        for index, row in accessibility_zones_df.iterrows():
            analysis_zone_id = row['zone_id']
            analysis_zone_description = row['zone_description']
            
            for index, row in zones_df.iterrows():
                zone_id = row['zone_id']
                cost_attribute='cost_minutes'
                demand=0
                #print(index, ": analysis_zone_id=", analysis_zone_id, analysis_zone_description, ", zone_id=", zone_id)
                try:
                    # To Driection
                    to_result_df = self.get_path(zone_id, analysis_zone_id, demand, cost_attribute)
                    to_result_df['analysis_direction'] = "To Analysis Zone"
                    to_result_df['analysis_zone_id'] = analysis_zone_id
                    to_result_df['opposite_zone_id'] = zone_id
                    to_result_df['analysis_zone_description'] = analysis_zone_description
                    self.path_outputs_df = pd.concat([self.path_outputs_df, to_result_df])
                    # From Driection
                    from_result_df = self.get_path(analysis_zone_id, zone_id, demand, cost_attribute)
                    from_result_df['analysis_direction'] = "From Analysis Zone"
                    from_result_df['analysis_zone_id'] = analysis_zone_id
                    from_result_df['opposite_zone_id'] = zone_id
                    from_result_df['analysis_zone_description'] = analysis_zone_description
                    self.path_outputs_df = pd.concat([self.path_outputs_df, from_result_df])
                except:
                    print("    An error occurred skimming {} {}".format(analysis_zone_id, analysis_zone_description))
            
        # Format output
        self.path_outputs_df['od_pair'] = self.path_outputs_df['origin_zone'].astype(str) + "_" + self.path_outputs_df['dest_zone'].astype(str)
        
        # Export dataframe to CSV
        accessibility_output_csv_fp = os.path.join(self.run_output_dir, 'accessibility_outputs.csv')
        self.path_outputs_df.to_csv(accessibility_output_csv_fp, index=False) 
        print("Exported outputs to ", accessibility_output_csv_fp)
        
        # Matrix output
        self.accessibility_matrix_df = self.path_outputs_df.groupby(['analysis_direction','analysis_zone_id','analysis_zone_description','opposite_zone_id','od_pair','origin_zone', 'dest_zone']).agg({'demand':'mean', 'length_metres':'sum'})
        self.accessibility_matrix_df.reset_index(inplace=True)
        self.accessibility_matrix_df['travel_time_minutes'] = (self.accessibility_matrix_df['length_metres']/1000)/20*60 # Assumes 20 km per cycle hour speed       
        self.accessibility_matrix_df = self.accessibility_matrix_df[['analysis_direction','analysis_zone_id','analysis_zone_description','opposite_zone_id','origin_zone', 'dest_zone','demand','length_metres','travel_time_minutes']]
        
        # Join WKT geometry
        zone_geom_df = zones_df[['zone_id','X','Y','WKT']]
        self.accessibility_matrix_geom_df = pd.merge(
            self.accessibility_matrix_df, 
            zone_geom_df, 
            how='inner', 
            left_on=['opposite_zone_id'], 
            right_on = ['zone_id']
        ) 
        
        # Export dataframe to CSV
        self.accessibility_matrix_output_csv_fp = os.path.join(self.run_output_dir, 'accessibility_matrix_outputs.csv')
        self.accessibility_matrix_geom_df.to_csv(self.accessibility_matrix_output_csv_fp, index=False) 
        print("Exported accessibility matrix output to ", self.accessibility_matrix_output_csv_fp)
        
        return self.accessibility_matrix_geom_df

