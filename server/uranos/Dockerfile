FROM ubuntu:22.04

# Install xclock and other necessary packages
RUN apt-get update && apt-get install -y x11-apps task-spooler python3-dev

RUN apt-get install -y wget unzip qtbase5-dev build-essential qt5-qmake git libtbb-dev 
WORKDIR /app/
RUN git clone https://gitlab.com/mkoehli/uranos.git
WORKDIR /app/uranos/
RUN wget https://gitlab.com/mkoehli/uranos/-/raw/main/data/ENDFdata.zip && unzip ENDFdata.zip 
RUN wget https://gitlab.com/mkoehli/uranos/-/blob/main/data/IncomingSpectrum.root -o ENDFdata/IncomingSpectrum.root
#RUN wget "https://gitlab.com/mkoehli/uranos/-/raw/main/binaries/UranosGUI_Ubuntu22_QT_5_15_3.zip?ref_type=heads" && \ 
#    unzip 'UranosGUI_Ubuntu22_QT_5_15_3.zip?ref_type=heads'
RUN wget https://root.cern/download/root_v6.30.02.Linux-ubuntu22.04-x86_64-gcc11.4.tar.gz && \
    tar -zxvf "root_v6.30.02.Linux-ubuntu22.04-x86_64-gcc11.4.tar.gz"
RUN qmake && make && make install
ENV LD_LIBRARY_PATH=/app/uranos/root/lib/

# Set the entrypoint to run xclock
ENTRYPOINT ["/bin/bash"]
