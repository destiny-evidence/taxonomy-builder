import "./Breadcrumb.css";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <ol class="breadcrumb__list">
        {items.map((item, index) => (
          <li key={index} class="breadcrumb__item">
            {index > 0 && <span class="breadcrumb__separator">/</span>}
            {item.href ? (
              <a href={item.href} class="breadcrumb__link">
                {item.label}
              </a>
            ) : (
              <span class="breadcrumb__current">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
