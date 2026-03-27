interface ProgressBarProps {
  value: number;
}

export function ProgressBar({ value }: ProgressBarProps) {
  const safeValue = Math.max(0, Math.min(100, value));
  return (
    <div className="progress-bar" aria-label={`Progress ${safeValue}%`}>
      <div className="progress-bar__fill" style={{ width: `${safeValue}%` }} />
    </div>
  );
}
