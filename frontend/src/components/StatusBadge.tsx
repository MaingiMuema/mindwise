interface StatusBadgeProps {
  label: string;
}

export function StatusBadge({ label }: StatusBadgeProps) {
  const tone = label.toLowerCase();
  return <span className={`status-badge status-badge--${tone}`}>{label.replace(/_/g, " ")}</span>;
}
