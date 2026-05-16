import { useEffect, useRef, useState } from 'react';

import { updateProjectRouteProjectsProjectIdPatch } from '../../api/client';

export function EditableProjectName({
  projectId,
  name,
  onSaved,
}: {
  projectId: string;
  name: string;
  onSaved: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(name);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setDraft(name);
  }, [name]);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  function startEditing() {
    setDraft(name);
    setError(null);
    setEditing(true);
  }

  function cancelEditing() {
    setDraft(name);
    setError(null);
    setEditing(false);
  }

  async function save() {
    if (saving) return;

    const trimmed = draft.trim();
    if (!trimmed) {
      setError('Project name is required.');
      return;
    }
    if (trimmed === name) {
      setEditing(false);
      setError(null);
      return;
    }

    setSaving(true);
    setError(null);

    const { error: apiError } = await updateProjectRouteProjectsProjectIdPatch({
      path: { project_id: projectId },
      body: { name: trimmed },
    });

    setSaving(false);

    if (apiError) {
      setError('Failed to save project name.');
      return;
    }

    setEditing(false);
    await onSaved();
  }

  if (editing) {
    return (
      <div>
        <input
          ref={inputRef}
          type="text"
          value={draft}
          disabled={saving}
          maxLength={500}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              void save();
            } else if (e.key === 'Escape') {
              e.preventDefault();
              cancelEditing();
            }
          }}
          onBlur={() => {
            void save();
          }}
          className="w-full rounded-lg border border-slate-300 px-2 py-1 text-lg font-semibold text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 disabled:opacity-60"
          aria-label="Project name"
        />
        {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
    );
  }

  return (
    <h2
      className="cursor-text text-lg font-semibold text-slate-900"
      title="Double-click to edit"
      onDoubleClick={startEditing}
    >
      {name}
    </h2>
  );
}
