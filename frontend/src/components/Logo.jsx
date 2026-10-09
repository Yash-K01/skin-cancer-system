export default function Logo({ size = 40 }) {
  return (
    <span className="logo" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="logoGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#14938a" />
            <stop offset="1" stopColor="#0b5a54" />
          </linearGradient>
        </defs>
        <rect width="48" height="48" rx="12" fill="url(#logoGrad)" />
        <rect x="1" y="1" width="46" height="23" rx="11" fill="#fff" opacity="0.12" />
        <path d="M21 11h6v10h10v6H27v10h-6V27H11v-6h10z" fill="#fff" />
        <circle cx="38" cy="10" r="3" fill="#99d5cf" />
      </svg>
    </span>
  );
}
