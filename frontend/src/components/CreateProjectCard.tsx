import { useState } from 'react';

import { createProjectProjectsPost } from '../api/client';

type CreateProjectCardProps = {
  onCreated: () => void;
};

export function CreateProjectCard({ onCreated }: CreateProjectCardProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function closeModal() {
    setOpen(false);
    setName('');
    setError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError('Project name is required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const { data, error: apiError } = await createProjectProjectsPost({
      body: { name: trimmed },
    });

    setSubmitting(false);

    if (apiError || !data) {
      const detail =
        apiError && typeof apiError === 'object' && 'detail' in apiError
          ? String((apiError as { detail: unknown }).detail)
          : 'Failed to create project.';
      setError(detail);
      return;
    }

    closeModal();
    onCreated();
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex min-h-[160px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-5 text-slate-600 transition hover:border-slate-400 hover:bg-slate-100 hover:text-slate-800"
      >
        <span className="text-3xl font-light leading-none text-slate-400">+</span>
        <span className="mt-2 text-sm font-medium">New project</span>
      </button>

      {open && (
        <Modal onClose={closeModal}>
          <h2 className="text-lg font-semibold text-slate-900">Create project</h2>
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div>
              <label htmlFor="project-name" className="block text-sm font-medium text-slate-700">
                Name
              </label>
              <input
                id="project-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
                maxLength={500}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
                placeholder="e.g. Route section A12"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={closeModal}
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {submitting ? 'Creating…' : 'Create'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}

function Modal({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="presentation"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}
