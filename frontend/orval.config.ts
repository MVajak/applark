import { defineConfig } from 'orval';

export default defineConfig({
  postpilot: {
    input: { target: 'http://localhost:8000/api/v1/openapi.json' },
    output: {
      mode: 'tags-split',
      target: 'src/api/generated/endpoints.ts',
      schemas: 'src/api/generated/model',
      client: 'react-query',
      httpClient: 'axios',
      mock: true,
      prettier: true,
      override: {
        mutator: { path: 'src/api/client.ts', name: 'customAxios' },
        query: { useQuery: true, options: { staleTime: 30_000 } },
      },
    },
  },
});
