FROM python:3.11.0

RUN groupadd -r appuser && useradd --no-log-init -m -r -g appuser appuser

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000

RUN chown -R appuser:appuser /app
USER appuser

CMD ["python" , "manage.py" , "runserver" , "0.0.0.0:8000"]