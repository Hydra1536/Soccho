import { ApolloClient, DefaultOptions, HttpLink, InMemoryCache, from } from '@apollo/client';
import { onError } from '@apollo/client/link/error';
import { setContext } from '@apollo/client/link/context';
import { ACCESS_TOKEN_KEY } from '../lib/api';

export type GatewayService = 'social' | 'transaction' | 'auth' | 'notification';

const GRAPHQL_URI = import.meta.env.VITE_GRAPHQL_URL || 'https://soccho-gateway.onrender.com/graphql/';

const httpLink = new HttpLink({
  uri: GRAPHQL_URI,
  credentials: 'include',
});

const authAndServiceLink = setContext((operation, context) => {
  const token = typeof window === 'undefined' ? null : localStorage.getItem(ACCESS_TOKEN_KEY);
  const service = (operation.getContext().service as GatewayService | undefined) || 'social';
  const headers = {
    ...(context.headers || {}),
    'X-Service': service,
  } as Record<string, string>;

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return { headers };
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
  link: from([errorLink, authAndServiceLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions,
});
