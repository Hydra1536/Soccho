import { createRoot } from "react-dom/client";
import { ApolloProvider } from '@apollo/client';
import App from "./app/App.tsx";
import { AppErrorBoundary } from './app/components/AppErrorBoundary';
import { apolloClient } from './graphql/client';
import "./styles/index.css";

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => undefined);
  });
}

createRoot(document.getElementById("root")!).render(
  <ApolloProvider client={apolloClient}>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </ApolloProvider>
);
