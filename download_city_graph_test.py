import osmnx as ox
import argparse

def download_graph(city_name):
    """
    Download the road graph of a city and save it in .graphml format.

    Args:
        city_name (str): City name (e.g., "Natal").

    Returns:
        None
    """
    try:
        # Format the city name with "Brazil" for better location accuracy
        formatted_city_name = f"{city_name}, Brazil"
        
        # Generate the filename automatically
        filename = f"{city_name.lower().replace(' ', '_')}.graphml"
        
        # Download the city graph with the desired network type (e.g., drive)
        print(f"Downloading the graph for the city: {formatted_city_name}")
        G = ox.graph_from_place(formatted_city_name, network_type="drive")

        # Saving the graph in .graphml format
        print(f"Saving the graph to the file: {filename}")
        ox.save_graphml(G, filename)

        print("Graph saved successfully!")
    except Exception as e:
        print(f"Error downloading or saving graph: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a city's road graph and save it as a .graphml file.")
    parser.add_argument("city_name", type=str, help="The name of the city (e.g., 'Natal').")
    args = parser.parse_args()

    # Run download and save
    download_graph(args.city_name)

