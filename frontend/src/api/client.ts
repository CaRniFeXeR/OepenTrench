import { client } from './generated/client.gen';

client.setConfig({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
});

export { client };
export {
  createProjectProjectsPost,
  listProjectsRouteProjectsGet,
  readProjectGeojsonProjectsProjectIdGeojsonGet,
  readProjectMapPhotosProjectsProjectIdMapPhotosGet,
  readProjectProjectsProjectIdGet,
  reviewProjectImageAnalysisProjectsProjectIdImagesAssetIdAnalysisPatch,
  updateProjectRouteProjectsProjectIdPatch,
  uploadProjectGeojsonProjectsProjectIdGeojsonPost,
  uploadProjectImageProjectsProjectIdImagesPost,
} from './generated/sdk.gen';
export type {
  GeojsonStatus,
  MapPhotoMarkerRead,
  PhotoAnalysisRead,
  PhotoAnalysisReviewUpdate,
  PhotoDocumentationCategory,
  ProjectAssetRead,
  ProjectDetailRead,
  ProjectRead,
  ProjectStatus,
} from './generated/types.gen';
