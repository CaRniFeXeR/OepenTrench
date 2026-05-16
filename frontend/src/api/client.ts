import { client } from './generated/client.gen';

client.setConfig({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
});

export { client };
export {
  createProjectProjectsPost,
  listProjectsRouteProjectsGet,
  readProjectGeojsonProjectsProjectIdGeojsonGet,
  readProjectProjectsProjectIdGet,
  updateProjectRouteProjectsProjectIdPatch,
  uploadProjectGeojsonProjectsProjectIdGeojsonPost,
  uploadProjectImageProjectsProjectIdImagesPost,
} from './generated/sdk.gen';
export type {
  GeojsonStatus,
  ProjectAssetRead,
  ProjectDetailRead,
  ProjectRead,
  ProjectStatus,
} from './generated/types.gen';
