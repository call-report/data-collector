FROM henningn/selenium-standalone-firefox:4.1.3-20220405
USER root
RUN apt update -y
RUN apt upgrade -y 
RUN apt install python3-pip -y
RUN pip install ipython
RUN pip install selenium
RUN pip install flask
RUN pip install tqdm
RUN pip install xmltodict
RUN pip install requests
RUN pip install pandas
USER seluser
WORKDIR /code
CMD [ "flask" , "run" , "--port", "8080", "--host","0.0.0.0"]