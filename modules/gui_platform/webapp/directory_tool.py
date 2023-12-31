def get_home():
    current_file = __file__
    current_path = __file__.strip(__file__.split("/")[-1])
    resources_folder = current_path
    return current_path

def get_assets():
    print("ASSET LOCATINO : ", get_home())
    return get_home() + "/assets/"

def get_store():
    return get_home() + "/store/"