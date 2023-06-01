FROM python:3.11

WORKDIR /code

COPY src/ /code/src
COPY requirements.txt /code/requirements.txt
COPY .env /.env
COPY pyproject.toml /code/pyproject.toml

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install /code/

CMD ["uvicorn", "ideabank_webapi:app", "--host", "0.0.0.0", "--port", "80"]
