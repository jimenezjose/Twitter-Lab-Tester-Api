FROM python:3.7-alpine
  
WORKDIR /usr/src/app

ENV FLASK_APP lab_tester
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 80
ENV FLASK_ENV development

RUN apk add --no-cache gcc musl-dev linux-headers

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["flask", "run"]
