FROM ubuntu:22.04 
RUN apt update 
RUN apt-get install -y libgdal-dev
RUN apt install -y gdal-bin python3-gdal
RUN apt install -y python3 python3-pip 
RUN python3 -m pip install colorama==0.4.6 dash==2.17.0 dash_bootstrap_components==1.5.0 dash_core_components==2.0.0 dash_draggable==0.1.2 dash_extensions==1.0.18 
RUN python3 -m pip install dash_html_components==2.0.0 dash_iconify==0.1.2 dash_leaflet==1.0.11 dash_mantine_components==0.12.1 
RUN python3 -m pip install fastapi==0.115.0 fastapi_utils==0.7.0 Flask==3.0.3 geojson==3.0.1 matplotlib==3.9.2 numpy==2.1.1 paho_mqtt==1.6.1 pandas==2.2.2 parse==1.19.1 
RUN python3 -m pip install PCSE==5.5.5 plotly==5.18.0 
RUN python3 -m pip install pmdarima==2.0.4 pvlib==0.10.3 pydantic==2.7.0 pydantic_settings==2.5.2 PyYAML==6.0.2 Requests==2.32.3 scikit_learn==1.3.1 
RUN python3 -m pip install scipy==1.14.1 statsmodels==0.14.1 
RUN python3 -m pip install uvicorn typing_inspect python-multipart pcse
RUN python3 -m pip install "fastapi[standard]" postgres  SQLALCHEMY==2.0.0
