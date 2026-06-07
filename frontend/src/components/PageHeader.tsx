interface PageHeaderProps {
  icon: string;
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}

export function PageHeader({ icon, title, subtitle, children }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header-inner">
        <span className="page-header-icon" aria-hidden>
          {icon}
        </span>
        <div className="page-header-text">
          <h1 className="page-header-title">{title}</h1>
          {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
        </div>
      </div>
      {children && <div className="page-header-actions">{children}</div>}
    </div>
  );
}
