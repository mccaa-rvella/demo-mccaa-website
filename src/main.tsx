import React, { StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App.tsx';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

const KBLayout = React.lazy(() => import('./kb/KBLayout.tsx'));
const KBLanding = React.lazy(() => import('./kb/KBLanding.tsx'));
const SourceViewer = React.lazy(() => import('./kb/SourceViewer.tsx'));
const AdminLayout = React.lazy(() => import('./admin/AdminLayout.tsx'));
const ArticleList = React.lazy(() => import('./admin/ArticleList.tsx'));
const TrendsDashboard = React.lazy(() => import('./admin/TrendsDashboard.tsx'));

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-pulse text-mccaa-teal text-lg">Loading...</div>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/kb" element={<KBLayout />}>
              <Route index element={<KBLanding />} />
              <Route path=":slug" element={<SourceViewer />} />
            </Route>
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<ArticleList />} />
              <Route path="articles" element={<ArticleList />} />
              <Route path="trends" element={<TrendsDashboard />} />
            </Route>
            <Route path="/*" element={<App />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
