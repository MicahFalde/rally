import { useState, useRef, useEffect } from "react";

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder?: string;
  width?: number;
}

export default function SearchableSelect({
  label,
  value,
  onChange,
  options,
  placeholder = "All",
  width = 160,
}: Props) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = options.filter((o) =>
    o.toLowerCase().includes(search.toLowerCase())
  );

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <label
        style={{
          display: "block",
          fontSize: 11,
          color: "#888",
          marginBottom: 2,
        }}
      >
        {label}
      </label>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        style={{
          width,
          padding: "6px 8px",
          border: "1px solid #ddd",
          borderRadius: 4,
          fontSize: 13,
          background: "#fff",
          textAlign: "left",
          cursor: "pointer",
          color: value ? "#000" : "#999",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span>{value || placeholder}</span>
        <span style={{ fontSize: 10, color: "#aaa" }}>
          {value ? "×" : "▾"}
        </span>
      </button>

      {/* Clear on click of × */}
      {value && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onChange("");
            setOpen(false);
          }}
          style={{
            position: "absolute",
            right: 8,
            top: 22,
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: 12,
            color: "#888",
            padding: "2px 4px",
          }}
        >
          ×
        </button>
      )}

      {open && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            width: Math.max(width, 200),
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: 4,
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            zIndex: 100,
            marginTop: 2,
          }}
        >
          <input
            ref={inputRef}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search..."
            style={{
              width: "100%",
              padding: "8px 10px",
              border: "none",
              borderBottom: "1px solid #eee",
              fontSize: 13,
              boxSizing: "border-box",
              outline: "none",
            }}
          />
          <div style={{ maxHeight: 200, overflowY: "auto" }}>
            {filtered.length === 0 ? (
              <div
                style={{ padding: "8px 10px", fontSize: 13, color: "#888" }}
              >
                No results
              </div>
            ) : (
              filtered.map((opt) => (
                <div
                  key={opt}
                  onClick={() => {
                    onChange(opt);
                    setOpen(false);
                    setSearch("");
                  }}
                  style={{
                    padding: "6px 10px",
                    fontSize: 13,
                    cursor: "pointer",
                    background: opt === value ? "#f0f4ff" : "transparent",
                    fontWeight: opt === value ? 600 : 400,
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "#f5f5f5")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background =
                      opt === value ? "#f0f4ff" : "transparent")
                  }
                >
                  {opt}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
