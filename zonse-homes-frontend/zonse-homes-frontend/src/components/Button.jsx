export function Button({ variant = "primary", size = "md", className = "", ...props }) {
  return <button className={`btn btn--${variant} btn--${size} ${className}`} {...props} />;
}

export function Badge({ tone, children }) {
  return <span className={`badge ${tone === "success" ? "badge--success" : ""}`}>{children}</span>;
}
