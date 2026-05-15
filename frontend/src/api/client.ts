import { client } from './generated/client.gen';

client.setConfig({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
});

export { client };
export {
  createProjectProjectsPost,
  listProjectsRouteProjectsGet,
} from './generated/sdk.gen';
export type { ProjectRead } from './generated/types.gen';
