docker build -t retail_demo . && \

ifconfig && \

docker run -it --gpus '"device=0"' -p 8118:8888 -p 5000:5000 --network=host -v /home/anallamothu/projects/retail_demo:/home/cuopt_user/projects/retail_demo retail_demo
