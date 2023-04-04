FROM nvcr.io/nvidia/cuopt/cuopt:22.12
ARG PYTHON_VERSION=3.8
EXPOSE 8888
EXPOSE 8118
EXPOSE 5000

#RUN pip install jupyterlab
# custom packages
#RUN conda install pytorch torchvision -c pytorch
#RUN conda update -y conda
#RUN conda init

RUN pip install --no-cache-dir --upgrade pip && pip install haversine && pip install folium && pip install pyrosm && pip install networkx && pip install igraph && pip install geopandas

# startup command
#CMD conda install jupyterlab
WORKDIR /home/cuopt_user/projects/retail_demo
#CMD jupyter notebook --allow-root --ip=0.0.0.0 --no-browser --NotebookApp.token=''


