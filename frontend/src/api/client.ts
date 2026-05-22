import axios, { type AxiosRequestConfig } from 'axios';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

export const customAxios = <T>(config: AxiosRequestConfig): Promise<T> =>
  instance(config).then((r) => r.data as T);
