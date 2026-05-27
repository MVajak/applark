import { createBrowserRouter } from 'react-router-dom';

import { CVPage } from '@/domains/cv/pages/CVPage';
import { HomePage } from '@/domains/home/pages/HomePage';
import { JobDetailPage } from '@/domains/jobs/pages/JobDetailPage';
import { JobsListPage } from '@/domains/jobs/pages/JobsListPage';
import { RootLayout } from '@/domains/shell/components/RootLayout';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'cv', element: <CVPage /> },
      { path: 'jobs', element: <JobsListPage /> },
      { path: 'jobs/:id', element: <JobDetailPage /> },
    ],
  },
]);
