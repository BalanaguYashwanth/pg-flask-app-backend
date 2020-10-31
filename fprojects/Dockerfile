FROM python:3.8.0

EXPOSE 5000


WORKDIR /app

COPY . /app


RUN pip3 install --upgrade pip

RUN pip3 --no-cache-dir install -r requirements.txt

RUN python3 -m pip install ptvsd

CMD ["python3","pg.py", "-m", "ptvsd", "--host", "0.0.0.0", "--port", "5678", "--wait", \
    "-m", "flask", "run", "--no-reload", "--no-debugger", "--host", "0.0.0.0", "--port", "5000"]

