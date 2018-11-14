FROM python:3.6-alpine

RUN adduser -D healthnote

WORKDIR /home/healthnote

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN apk add --no-cache --virtual .pynacl_deps build-base python3-dev libffi-dev postgresql-dev
RUN venv/bin/pip install --upgrade pip
RUN venv/bin/pip install --upgrade setuptools
RUN venv/bin/pip install -r requirements.txt


COPY app app
# COPY migrations migrations
COPY healthnote.py config.py boot.sh ./
# Set boot.sh as an executable file
RUN chmod a+x boot.sh

ENV FLASK_APP healthnote.py
ENV SECRET_KEY secretbentley
ENV MAIL_SERVER smtp.googlemail.com 
ENV MAIL_PORT 587  
ENV MAIL_USE_TLS true
ENV MAIL_USERNAME healthwebbentley 
ENV MAIL_PASSWORD bentleyhealthweb 
ENV ADMINS ['healthwebbentley@gmail.com']
ENV DATABASE_URL mysql+pymysql://healthwebbentley:bentleyhealthweb@myhealthnotes1.coew39c5vrza.us-east-1.rds.amazonaws.com/health_test1 

# Let user "healthnote" work with all the commands(default user is "root")
RUN chown -R healthnote:healthnote ./
USER healthnote

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
