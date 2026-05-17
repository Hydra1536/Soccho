import { ApolloClient, ApolloLink, DefaultOptions, HttpLink, InMemoryCache } from '@apollo/client';
import { Observable } from '@apollo/client/core';
import type { FetchResult, NextLink, Operation } from '@apollo/client/core';
import { onError } from '@apollo/client/link/error';
import type { ErrorResponse } from '@apollo/client/link/error';
import { buildAuthorizationHeader, getValidAccessToken, redirectToLogin, refreshAccessToken } from '../lib/api';

export type GatewayService = 'social' | 'transaction' | 'auth' | 'notification';

const GRAPHQL_URI = import.meta.env.VITE_GRAPHQL_URL || 'https://soccho-gateway.onrender.com/graphql/';

const httpLink = new HttpLink({
  uri: GRAPHQL_URI,
  credentials: 'include',
});

const authAndServiceLink = new ApolloLink((operation: Operation, forward: NextLink) => {
  return new Observable<FetchResult>((observer) => {
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
      const runtimeToken = await getValidAccessToken();
      const authorizationValue = buildAuthorizationHeader(runtimeToken);
      const restHeaders = { ...(currentContext.headers || {}) };
      delete restHeaders.authorization;
      delete restHeaders.Authorization;

      operation.setContext({
        ...currentContext,
        headers: {
          ...restHeaders,
          'X-Service': service,
          ...(authorizationValue
            ? {
                authorization: authorizationValue,
                Authorization: authorizationValue,
              }
            : {}),
        },
      });

      subscription = forward(operation).subscribe({
        next: (value) => observer.next(value),
        error: (error) => observer.error(error),
        complete: () => observer.complete(),
      });
    };

    void run().catch((error) => {
      observer.error(error);
    });

    return () => {
      subscription?.unsubscribe?.();
    };
  });
});

function getNetworkStatusCode(networkError: unknown): number | null {
  if (!networkError || typeof networkError !== 'object') {
    return null;
  }

  const withStatusCode = networkError as { statusCode?: unknown; status?: unknown };
  if (typeof withStatusCode.statusCode === 'number') {
    return withStatusCode.statusCode;
  }

  if (typeof withStatusCode.status === 'number') {
    return withStatusCode.status;
  }

  return null;
}

const unauthorizedRetryLink = onError((errorResponse: ErrorResponse) => {
  const { networkError, operation, forward } = errorResponse;
  const statusCode = getNetworkStatusCode(networkError);
  const context = operation.getContext() as { _didAuthRetry?: boolean };

  if (statusCode !== 401 || context._didAuthRetry || !forward) {
    return undefined;
  }

  operation.setContext({
    ...context,
    _didAuthRetry: true,
  });

  return new Observable<FetchResult>((observer) => {
    void (async () => {
      const refreshedAccessToken = await refreshAccessToken();
      if (!refreshedAccessToken) {
        redirectToLogin();
        observer.error(networkError);
        return;
      }

      const existingContext = operation.getContext() as { headers?: Record<string, string> };
      const nextHeaders = { ...(existingContext.headers || {}) };
      const authHeader = buildAuthorizationHeader(refreshedAccessToken);
      nextHeaders.authorization = authHeader;
      nextHeaders.Authorization = authHeader;
      operation.setContext({
        ...existingContext,
        headers: nextHeaders,
      });

      forward(operation).subscribe({
        next: (value) => observer.next(value),
        error: (error) => observer.error(error),
        complete: () => observer.complete(),
      });
    })().catch((retryError) => {
      observer.error(retryError);
    });
  });
});

const errorLink = onError((errorResponse: ErrorResponse) => {
  const { graphQLErrors, networkError, operation } = errorResponse;
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
  link: ApolloLink.from([unauthorizedRetryLink, errorLink, authAndServiceLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions,
});
