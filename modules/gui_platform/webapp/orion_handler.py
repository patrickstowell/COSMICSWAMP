
import requests
import json

class orion_handler:
    def __init__(self):
        self.orion_host  = "http://localhost"
        self.orion_port  = "1026"
        self.servicepath = "/sensor_data"
        self.service      = "openiot"

    def get_entities(self):
        url = f"{self.orion_host}:{self.orion_port}/v2/entities?option=keyValues&limit=1000"
        headers = {
            "Fiware-Service": self.service,
            "Fiware-Servicepath": self.servicepath
            }
        try:
            r = requests.get(url, headers=headers, timeout=1)
        except:
            return {"error": "Failed to connect to server"}
        
        rtext = r.text.replace(".,",",")
        vals = json.loads(rtext)
        
        return vals
    
    def get_entity_attrs(self, entity):
        
        url = f"{self.orion_host}:{self.orion_port}/v2/entities/{entity}/attrs"
        print("ATTR", url)
        headers = {
            "Fiware-Service": self.service,
            "Fiware-Servicepath": self.servicepath
            }
        
        #print(url, headers)
        try:
            r = requests.get(url, headers=headers, timeout=1)
        except:
            return {"error": "Failed to connect to server"}
        
        
        rtext = r.text.replace(".,",",")
        vals = json.loads(rtext)
        
        return vals
        
    def update_entity_attrs(self, entity, data):
        """Updates ORION context

        Args:
            entity (str): Entity ID
            data (dict): NGSI dictionary for the data update.
        """
        url = f"{self.orion_host}:{self.orion_port}/v2/entities/{entity}/attrs"

        headers = {
            "Content-Type": "application/json",
            "Fiware-Service": self.service,
            "Fiware-Servicepath": self.servicepath
            }

        # Submit
        r = requests.post(url, headers=headers, json=data, timeout=1)
        # print(r.text)
        # print(r.status_code)
        return 
        
ORION = orion_handler()
