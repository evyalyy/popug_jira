from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.utils.timezone import make_aware

from .models import Employee, TaskFact
from accounting.models import TransactionKind
from auth_service.models import Role

import threading
from datetime import datetime, timedelta
from kafka import KafkaConsumer

from common.event_utils import consume_events
from common.events.cud import AccountCreatedCUDv2, AccountChangedCUDv2, TaskCostAssigned, TransactionCreated
from common.schema_registry import SchemaRegistry
from .event_handlers import *
from common.authorized_only import authorized_only

registry = SchemaRegistry()
registry.register(2, AccountCreatedCUDv2, AccountCreatedHandlerV2)
registry.register(2, AccountChangedCUDv2, AccountChangedHandlerV2)
registry.register(1, TaskCostAssigned, TaskCostAssignedHandler)
registry.register(1, TransactionCreated, TransactionCreatedHandler)


accounts_consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])
tasks_consumer = KafkaConsumer('tasks', bootstrap_servers=[settings.KAFKA_HOST])
transactions_consumer = KafkaConsumer('transactions', bootstrap_servers=[settings.KAFKA_HOST])

thr = threading.Thread(target=consume_events, args=(accounts_consumer, registry, 'analytics'))
thr.start()
thr2 = threading.Thread(target=consume_events, args=(tasks_consumer, registry, 'analytics'))
thr2.start()
thr3 = threading.Thread(target=consume_events, args=(transactions_consumer, registry, 'analytics'))
thr3.start()


class MinusByEmployee(object):

    def __init__(self, name):
        self.name = name
        self.amount = 0

    def __str__(self):
        return 'MinusByEmployee(name={},amount={})'.format(self.name,self.amount)

    def __repr__(self):
        return self.__str__()


class MostExpensiveTask(object):

    def __init__(self, period_start, period_end, readable_period, fact):
        self.period_start = period_start
        self.period_end = period_end
        self.readable_period = readable_period
        self.fact = fact
        if self.fact is None:
            self.human_readable = 'No tasks'
        else:
            self.human_readable = 'Most expensive task for {} (from {} to {}): cost = {}, description = {}'.format(self.readable_period,
                                                                                                    self.period_start, self.period_end,
                                                                                                    self.fact.task.cost_close,
                                                                                                    self.fact.task.description)


def get_start_of_day(now):
    return datetime(now.year, now.month, now.day)

def get_today(now):
    return (get_start_of_day(now), now, 'today')

def get_last_week(now):
    return (now - timedelta(days=7), now, 'last week')

def get_last_month(now):
    return (now - timedelta(days=30), now, 'last month')


def select_facts_in_time_range(now, range_func, **kwargs):
    start, end, _ = range_func(now)
    return TaskFact.objects.filter(fact_ts__gte=make_aware(start),
                                   fact_ts__lte=make_aware(end),
                                   **kwargs)


def get_most_expensive_task(now, range_func, **kwargs):
    start, end, readable_period = range_func(now)
    facts = TaskFact.objects.filter(fact_ts__gte=make_aware(start),
                                    fact_ts__lte=make_aware(end),
                                    **kwargs)
    most_expensive = None
    if len(facts) > 0:
        most_expensive = max(facts, key=lambda fact: fact.task.cost_close)

    return MostExpensiveTask(start, end, readable_period, most_expensive)


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN])
def index(request):
    employees = Employee.objects.all()
    now = datetime.now()

    facts = select_facts_in_time_range(now, get_today, kind=TransactionKind.TASK_ASSIGNED)

    minus_by_employee = {}
    for fact in facts:
        if not fact.assignee.id in minus_by_employee:
            minus_by_employee[fact.assignee.id] = MinusByEmployee(fact.assignee.name)
        minus_by_employee[fact.assignee.id].amount += fact.task.cost_assign

    total_minus = sum(map(lambda v: v.amount,minus_by_employee.values())) if len(minus_by_employee) > 0 else 0

    most_expensive_today = get_most_expensive_task(now, get_today, kind=TransactionKind.TASK_CLOSED)
    most_expensive_last_week = get_most_expensive_task(now, get_last_week, kind=TransactionKind.TASK_CLOSED)
    most_expensive_last_month = get_most_expensive_task(now, get_last_month, kind=TransactionKind.TASK_CLOSED)
    return render(request, 'analytics/index.html', {'minus_by_employee': minus_by_employee.values(),
                                                    'total_minus': total_minus,
                                                    'most_expensive_today': most_expensive_today,
                                                    'most_expensive_last_week': most_expensive_last_week,
                                                    'most_expensive_last_month': most_expensive_last_month})
