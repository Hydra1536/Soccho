import { ApolloClient, ApolloLink, DefaultOptions, HttpLink, InMemoryCache } from '@apollo/client';
import { onError } from '@apollo/client/link/error';
import { ACCESS_TOKEN_KEY } from '../lib/api';

export type GatewayService = 'social' | 'transaction' | 'auth' | 'notification';

const GRAPHQL_URI = import.meta.env.VITE_GRAPHQL_URL || 'https://soccho-gateway.onrender.com/graphql/';

const httpLink = new HttpLink({
  uri: GRAPHQL_URI,
  credentials: 'include',
});

const authAndServiceLink = new ApolloLink((operation, forward) => {
  const token = typeof window === 'undefined' ? null : localStorage.getItem(ACCESS_TOKEN_KEY);
  const currentContext = operation.getContext() as {
    headers?: Record<string, string>;
    service?: GatewayService;
  };
  const service = currentContext.service || 'social';
  const headers: Record<string, string> = {
    ...(currentContext.headers || {}),
    'X-Service': service,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  operation.setContext({
    ...currentContext,
    headers,
  });

  return forward(operation);
});

const errorLink = onError(({ graphQLErrors, networkError, operation }) => {
  if (graphQLErrors?.length) {
    console.error(`GraphQL error in ${operation.operationName || 'anonymous operation'}`, graphQLErrors);
  }
  if (networkError) {
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
