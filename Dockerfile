FROM python:3.8
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/sexnine/yipy.git
CMD python ./main.py
