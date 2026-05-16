import type { PhotoDocumentationCategory, ProjectAssetRead } from '../../../api/client';
import { PHOTO_DOC_CATEGORIES } from '../../project-images/photoDocumentationCategories';
import { projectImageContentUrl } from '../../project-map/imageContentUrl';

export function CategorySampleStrip({
  projectId,
  samples,
}: {
  projectId: string;
  samples: Record<PhotoDocumentationCategory, ProjectAssetRead | null>;
}) {
  return (
    <div className="mt-4">
      <h4 className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Sample photos
      </h4>
      <div className="mt-2 grid grid-cols-3 gap-2">
        {PHOTO_DOC_CATEGORIES.map((cat) => {
          const asset = samples[cat.id];
          return (
            <div key={cat.id} className="flex flex-col gap-1">
              <div
                className={`flex aspect-square items-center justify-center overflow-hidden rounded-lg border border-slate-200 ${cat.banner.bgClass}`}
              >
                {asset ? (
                  <img
                    src={projectImageContentUrl(projectId, asset.id)}
                    alt={asset.original_label}
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <span className="px-2 text-center text-xs text-slate-500">No photo</span>
                )}
              </div>
              <p className={`truncate text-center text-xs font-medium ${cat.banner.textClass}`}>
                {cat.label}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
