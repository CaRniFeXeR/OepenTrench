import { useParams } from 'react-router-dom';

import { ProjectDetailLayout } from '../components/project-detail/layout/ProjectDetailLayout';
import { ProjectDetailHeader } from '../components/project-detail/layout/ProjectDetailHeader';
import { useProjectDetail } from '../components/project-detail/useProjectDetail';

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { project, loading, error, uploadsBusy, setUploadsBusy, refreshProject } =
    useProjectDetail(projectId);

  return (
    <div className="flex min-h-screen flex-col bg-slate-100 print:min-h-0">
      <ProjectDetailHeader uploadsBusy={uploadsBusy} />

      <main className="flex flex-1 flex-col">
        {loading && (
          <p className="print:hidden px-6 py-8 text-slate-500">Loading project…</p>
        )}
        {error && (
          <div className="print:hidden mx-4 mt-8 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 sm:mx-6">
            {error}
          </div>
        )}
        {!loading && !error && project && (
          <ProjectDetailLayout
            project={project}
            uploadsBusy={uploadsBusy}
            onRefresh={refreshProject}
            onUploadsBusyChange={setUploadsBusy}
          />
        )}
      </main>
    </div>
  );
}
