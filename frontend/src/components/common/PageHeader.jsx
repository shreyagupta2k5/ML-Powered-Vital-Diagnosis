export default function PageHeader({ title, breadcrumb }) {
  return (
    <div style={{ marginBottom: "1.5rem" }}>
      {breadcrumb && (
        <div style={{ fontSize: 12, color: "#aaa", marginBottom: 4 }}>
          {breadcrumb.map((crumb, i) => (
            <span key={i}>
              {i > 0 && <span style={{ margin: "0 6px" }}>›</span>}
              <span>{crumb}</span>
            </span>
          ))}
        </div>
      )}
      <h2 style={{ fontSize: 20, fontWeight: 600, color: "#111", margin: 0 }}>
        {title}
      </h2>
    </div>
  );
}