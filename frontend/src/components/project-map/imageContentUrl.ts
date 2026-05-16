export function projectImageContentUrl(
  projectId: string,
  assetId: string,
): string {
  return `/projects/${projectId}/images/${assetId}/content`;
}
