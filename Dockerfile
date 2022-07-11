FROM henningn/selenium-standalone-firefox:4.1.3-20220405
USER root
RUN apt update -y
RUN apt upgrade -y 
RUN apt install python3-pip -y
RUN pip install ipython
RUN pip install selenium
RUN pip install flask
USER seluser
# RUN apt update
# RUN apt install dialog apt-utils -y
# RUN apt -y upgrade
# RUN apt install wget bzip2 -y
# WORKDIR /root

# RUN apt install -y gnupg
# RUN apt install -y tzdata



# RUN apt install python3-pip -y
# RUN pip3 install tqdm
# RUN pip3 install selenium
# RUN pip3 install boto3


# RUN apt remove python3-pip -y
# RUN apt autoremove -y
# COPY $PWD/code/main.py /root/main.py
# CMD ["python3","/root/main.py"]
