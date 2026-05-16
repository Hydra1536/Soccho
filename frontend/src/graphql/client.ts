import { ApolloClient, ApolloLink, DefaultOptions, HttpLink, InMemoryCache } from '@apollo/client';
import { Observable } from '@apollo/client/core';
import { onError } from '@apollo/client/link/error';
import { getValidAccessToken, redirectToLogin } from '../lib/api';

export type GatewayService = 'social' | 'transaction' | 'auth' | 'notification';

const GRAPHQL_URI = import.meta.env.VITE_GRAPHQL_URL || 'https://soccho-gateway.onrender.com/graphql/';

const httpLink = new HttpLink({
  uri: GRAPHQL_URI,
  credentials: 'include',
});

const authAndServiceLink = new ApolloLink((operation, forward) => {
  return new Observable((observer) => {
    let subscription: { unsubscribe?: () => void } | undefined;

    const run = async () => {
      if (!forward) {
        observer.error(new Error('GraphQL transport unavailable'));
        return;
      }

      const currentContext = operation.getContext() as {
        headers?: Record<string, string>;
        service?: GatewayService;
      };
      const service = currentContext.service || 'social';
      const token = await getValidAccessToken();

      if (!token) {
        if (typeof window !== 'undefined') {
          redirectToLogin();
        }
        observer.error(new Error('Authentication required'));
        return;
      }

      operation.setContext({
        ...currentContext,
        headers: {
          ...(currentContext.headers || {}),
          'X-Service': service,
          authorization: token ? `Bearer ${token}` : '',
        },
      });

      subscription = forward(operation).subscribe({
        next: (value) => observer.next(value),
        error: (error) => observer.error(error),
        complete: () => observer.complete(),
      });
    };

    void run().catch((error) => {
      if (typeof window !== 'undefined') {
        redirectToLogin();
      }
      observer.error(error);
    });

    return () => {
      subscription?.unsubscribe?.();
    };
  });
});

const errorLink = onError(({ graphQLErrors, networkError, operation }) => {
  if (graphQLErrors?.length) {
    console.error(`GraphQL error in ${operation.operationName || 'anonymous operation'}`, graphQLErrors);
  }
  if (networkError) {
    const statusCode = typeof networkError === 'object' && networkError && 'statusCode' in networkError
      ? (networkError as { statusCode?: number }).statusCode
      : undefined;
    if (statusCode === 401 && typeof window !== 'undefined') {
      redirectToLogin();
    }
    console.error(`Network error in ${operation.operationName || 'anonymous operation'}`, networkError);
  }
});

const defaultOptions: DefaultOptions = {
  watchQuery: {
    fetchPolicy: 'cache-and-network',
    nextFetchPolicy: 'cache-first',
    errorPolicy: 'all',
  },
  query: {
    fetchPolicy: 'network-only',
    errorPolicy: 'all',
  },
};

export const apolloClient = new ApolloClient({
  link: ApolloLink.from([errorLink, authAndServiceLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions,
});
