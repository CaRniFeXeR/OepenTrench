export function PanelBackLink({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="mb-3 text-left text-sm font-medium text-violet-700 hover:text-violet-900"
    >
      {label}
    </button>
  );
}
