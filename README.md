# What is that

Educational project of task tracker. Implemented as a group of services.

Scheme of domains and services, along with events, produced and consumed by services:

![domains and event scheme](popug_event_storming_domain_model.jpg)


# How to run
* Create virualenv `python3 -m venv .venv`, activate it via `source .venv/bin/activate`
* Install packages `pip3 install django kafka-python django-log-request-id pydantic pyjwt`
* Execute `docker-compose up`, wait for Kafka brokers to start. If failed to start, shut down docker, wait for 20 seconds and try again. I don't know how to configure Kafka properly
* `source .venv/bin/activate && cd popug_jira && ./manage.py runserver`
