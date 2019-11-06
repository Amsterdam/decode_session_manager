FROM python:3.7
#COPY ./server/requirements.txt ./
COPY ./server /server
WORKDIR /server
RUN pip install -r requirements.txt
CMD python api.py
