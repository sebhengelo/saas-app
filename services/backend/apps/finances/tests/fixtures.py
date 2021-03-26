import pytest
import pytest_factoryboy
import stripe
from django.contrib.auth import get_user_model
from django.db import models as django_models

from . import factories
from .. import constants

User = get_user_model()

pytest_factoryboy.register(factories.CustomerFactory)
pytest_factoryboy.register(factories.BalanceTransactionFactory)
pytest_factoryboy.register(factories.ChargeFactory)
pytest_factoryboy.register(factories.PaymentIntentFactory)
pytest_factoryboy.register(factories.PaymentMethodFactory)
pytest_factoryboy.register(factories.PriceFactory)
pytest_factoryboy.register(factories.PlanFactory)
pytest_factoryboy.register(factories.ProductFactory)
pytest_factoryboy.register(factories.SubscriptionFactory)
pytest_factoryboy.register(factories.SubscriptionItemFactory)
pytest_factoryboy.register(factories.SubscriptionScheduleFactory)


@pytest.fixture(autouse=True)
def mock_init_user(mocker):
    mocker.patch('apps.finances.services.subscriptions.initialize_user')


@pytest.fixture()
def stripe_methods_factory(mocker):
    def fn(model, factory, request=None):
        def mock_stripe_instance(instance):
            stripe_instance = mocker.MagicMock()

            def getitem(*args, **kwargs):
                return instance.__dict__.__getitem__(*args, **kwargs)

            def base_request(method, url, params):
                if request:
                    request(instance, method, url, params)
                    return stripe_instance

                if method == 'post':
                    ignore_fields = ["date_purged", "subscriber"]
                    for field in model._meta.fields:
                        if field.name.startswith("djstripe_") or field.name in ignore_fields:
                            continue

                        field_data = params.get(field.name, None)
                        if field_data and not isinstance(field, django_models.ForeignKey):
                            setattr(instance, field.name, field_data)
                    instance.save()

                return stripe_instance

            def delete(**kwargs):
                instance.delete()
                return stripe_instance

            stripe_instance._wrapped_instance = instance
            stripe_instance.__getitem__.side_effect = getitem
            stripe_instance.request.side_effect = base_request
            stripe_instance.delete.side_effect = delete
            return stripe_instance

        def retrieve(id, **kwargs):
            instance = model.objects.get(id=id)
            return mock_stripe_instance(instance)

        def create(**kwargs):
            kwargs.pop('api_key', None)
            kwargs.pop('idempotency_key', None)
            kwargs.pop('stripe_account', None)
            kwargs.pop('metadata', None)

            instance = factory(**kwargs)
            return mock_stripe_instance(instance)

        return {'retrieve': retrieve, 'create': create}

    return fn


@pytest.fixture(scope='function', autouse=True)
def free_plan_price(price_factory, plan_factory):
    price = price_factory(
        product__name=constants.FREE_PLAN.name,
        unit_amount=constants.FREE_PLAN.initial_price.unit_amount,
        currency=constants.FREE_PLAN.initial_price.currency,
        recurring=constants.FREE_PLAN.initial_price.recurring,
    )

    plan_factory(
        id=price.id,
        product=price.product,
        amount=constants.FREE_PLAN.initial_price.unit_amount,
        currency=constants.FREE_PLAN.initial_price.currency,
    )

    return price


@pytest.fixture(scope='function', autouse=True)
def monthly_plan_price(price_factory, plan_factory):
    price = price_factory(
        product__name=constants.MONTHLY_PLAN.name,
        unit_amount=constants.MONTHLY_PLAN.initial_price.unit_amount,
        currency=constants.MONTHLY_PLAN.initial_price.currency,
        recurring=constants.MONTHLY_PLAN.initial_price.recurring,
    )

    plan_factory(
        id=price.id,
        product=price.product,
        amount=constants.MONTHLY_PLAN.initial_price.unit_amount,
        currency=constants.MONTHLY_PLAN.initial_price.currency,
    )

    return price


@pytest.fixture(scope='function', autouse=True)
def yearly_plan_price(price_factory, plan_factory):
    price = price_factory(
        product__name=constants.YEARLY_PLAN.name,
        unit_amount=constants.YEARLY_PLAN.initial_price.unit_amount,
        currency=constants.YEARLY_PLAN.initial_price.currency,
        recurring=constants.YEARLY_PLAN.initial_price.recurring,
    )

    plan_factory(
        id=price.id,
        product=price.product,
        amount=constants.YEARLY_PLAN.initial_price.unit_amount,
        currency=constants.YEARLY_PLAN.initial_price.currency,
    )

    return price


@pytest.fixture(scope='function', autouse=True)
def stripe_proxy():
    stripe.api_base = "http://stripemock:12111"