from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class PlatformSettings(BaseSettings):

    crate_host:   str = str(os.environ['CRATE_HOST'])
    crate_port:  int = int(os.environ['CRATE_PORT'])
    orion_host:   str = str(os.environ['ORION_HOST']) 
    orion_port:  int = int(os.environ['ORION_PORT']) 
    orion_url: str = str("")
    crate_url: str = str("")
    crate_pd: str = str("")

    application_port : int = int(os.environ["COSMICSWAMP_PORT"])

    def initialize(self):

        # Define dynamic global settings
        self.orion_url = f"{self.orion_host}:{self.orion_port}"
        self.crate_url = f"{self.crate_host}:{self.crate_port}"

        if not self.orion_url.startswith("http"): self.orion_url = "http://" + self.orion_url
        if not self.crate_url.startswith("http"): self.crate_url = "http://" + self.crate_url

        self.crate_pd = self.crate_url.replace("http","crate")
        
@lru_cache()
def settings():
    temp_settings = PlatformSettings()
    temp_settings.initialize()
    return temp_settings
