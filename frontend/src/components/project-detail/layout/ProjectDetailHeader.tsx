import { Link } from 'react-router-dom';

export function ProjectDetailHeader({ uploadsBusy }: { uploadsBusy: boolean }) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="px-4 py-4 sm:px-6">
        <Link
          to="/"
          aria-disabled={uploadsBusy}
          onClick={(e) => {
            if (uploadsBusy) e.preventDefault();
          }}
          className={`text-sm font-medium text-slate-600 hover:text-slate-900 ${
            uploadsBusy ? 'pointer-events-none opacity-50' : ''
          }`}
        >
          ← Back to projects
        </Link>
      </div>
    </header>
  );
}
