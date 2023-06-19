import { useQuery } from '@apollo/client';
import { StripeSubscriptionQueryQuery, getFragmentData } from '@sb/webapp-api-client/graphql';
import { Link } from '@sb/webapp-core/components/buttons';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@sb/webapp-core/components/cards';
import { useGenerateLocalePath } from '@sb/webapp-core/hooks';
import { mapConnection } from '@sb/webapp-core/utils/graphql';
import { FormattedMessage } from 'react-intl';

import { StripePaymentMethodInfo } from '../../components/stripe/stripePaymentMethodInfo';
import { RoutesConfig } from '../../config/routes';
import { subscriptionActivePlanDetailsQuery, subscriptionActiveSubscriptionFragment } from '../../hooks';

export type PaymentMethodContentProps = {
  allPaymentMethods?: StripeSubscriptionQueryQuery['allPaymentMethods'];
};

export const PaymentMethodContent = ({ allPaymentMethods }: PaymentMethodContentProps) => {
  const generateLocalePath = useGenerateLocalePath();

  const { data } = useQuery(subscriptionActivePlanDetailsQuery);
  const activeSubscription = getFragmentData(subscriptionActiveSubscriptionFragment, data?.activeSubscription);

  const paymentMethods = mapConnection((plan) => plan, allPaymentMethods);
  const defaultMethod =
    (activeSubscription && paymentMethods.find(({ id }) => id === activeSubscription.defaultPaymentMethod?.id)) ||
    paymentMethods[0];

  const renderCardDetails = () => (
    <Card>
      <CardHeader>
        <CardTitle>
          <FormattedMessage defaultMessage="Current method:" id="My subscription / Current method" />
        </CardTitle>
        <CardDescription>
          <FormattedMessage defaultMessage="Credit card" id="My subscription / Credit card" />
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="p-2 border rounded-md bg-secondary">
          <StripePaymentMethodInfo method={defaultMethod} />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-3">
      {defaultMethod && renderCardDetails()}
      <Link to={generateLocalePath(RoutesConfig.subscriptions.paymentMethod)} variant="default">
        {paymentMethods.length ? (
          <FormattedMessage defaultMessage="Edit payment methods" id="My subscription / Edit payment method button" />
        ) : (
          <FormattedMessage defaultMessage="Add payment methods" id="My subscription / Add payment method button" />
        )}
      </Link>
    </div>
  );
};
