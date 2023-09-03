FROM python:3.10-slim-buster

RUN pip3 install pipenv

ENV PROJECT_DIR /usr/src/bookingService

WORKDIR ${PROJECT_DIR}

COPY Pipfile .

COPY Pipfile.lock .

COPY . .

RUN pipenv install --deploy --ignore-pipfile

EXPOSE 5000

#CMD ["bash"]
CMD ["pipenv", "run", "python", "dbs.py"]