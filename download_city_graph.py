import osmnx as ox

def download_graph(city_name, filename):
    """
    Download the road graph of a city and save them in .graphml format.

    Args:
        city_name (str): City name (ex.: "São Paulo, Brazil").
        filename (str): File name .graphml to save the graph.

    Returns:
        None
    """
    try:
        # Download the city graph with the desired kind of network (ex.: drive, walk, etc.)
        print(f"Downloading the graph to the city: {city_name}")
        G = ox.graph_from_place(city_name, network_type="drive")

        # Saving the graph in .graphml format
        print(f"Saving the graph in the file: {filename}")
        ox.save_graphml(G, filename)

        print("Graph saved successfully!")
    except Exception as e:
        print(f"Error downloading or saving graph: {e}")

if __name__ == "__main__":
    # City and file name
    city_name = "Manaus, Brazil"  # Set city name
    filename = "manaus.graphml"   # File name to save

    # Run download and save
    download_graph(city_name, filename)
