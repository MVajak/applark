import { defineConfig } from 'orval';

export default defineConfig({
  applark: {
    input: { target: 'http://localhost:8000/api/v1/openapi.json' },
    output: {
      mode: 'tags-split',
      target: 'src/domains/api/generated/endpoints.ts',
      schemas: 'src/domains/api/generated/model',
      client: 'react-query',
      httpClient: 'axios',
      mock: true,
      prettier: true,
      override: {
        mutator: { path: 'src/domains/api/client.ts', name: 'customAxios' },
        query: { useQuery: true, options: { staleTime: 30_000 } },
      },
    },
  },
});
