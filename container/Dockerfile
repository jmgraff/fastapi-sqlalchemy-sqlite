from python

copy ./requirements.txt .
run pip install -r requirements.txt && rm requirements.txt

copy ./src /opt/container

workdir /opt/container

entrypoint ["python", "main.py"]
