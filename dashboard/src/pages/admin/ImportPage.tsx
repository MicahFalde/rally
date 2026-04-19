import { useState, useRef } from "react";
import api from "../../api/client";

const STATES: Record<string, string> = {
  OH: "Ohio",
};

export default function ImportPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState("OH");
  const [file, setFile] = useState<File | null>(null);
  const [geocode, setGeocode] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setResult(null);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post(
        `/admin/voter-files/import?state_code=${state}&geocode=${geocode}`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 600000, // 10 min — large files take time
        }
      );
      setResult(res.data);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err: any) {
      setError(err.response?.data?.detail || "Import failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 8px", fontSize: 22 }}>Import Voter File</h2>
      <p style={{ color: "#666", fontSize: 14, margin: "0 0 24px" }}>
        Upload a state voter file to add voters to the database. Ohio files can
        be downloaded from the{" "}
        <a
          href="https://www6.ohiosos.gov/ords/f?p=VOTERFTP:HOME"
          target="_blank"
          rel="noreferrer"
          style={{ color: "#4361ee" }}
        >
          Ohio Secretary of State
        </a>
        .
      </p>

      <form
        onSubmit={handleUpload}
        style={{
          background: "#fff",
          borderRadius: 8,
          padding: 24,
          maxWidth: 500,
        }}
      >
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
            State
          </label>
          <select
            value={state}
            onChange={(e) => setState(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 10px",
              border: "1px solid #ddd",
              borderRadius: 4,
              fontSize: 14,
              boxSizing: "border-box",
            }}
          >
            {Object.entries(STATES).map(([code, name]) => (
              <option key={code} value={code}>
                {name} ({code})
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
            Voter File
          </label>
          <input
            ref={fileRef}
            type="file"
            accept=".txt,.csv,.tsv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            style={{ fontSize: 14 }}
          />
          {file && (
            <div style={{ marginTop: 4, fontSize: 12, color: "#888" }}>
              {file.name} — {(file.size / 1024 / 1024).toFixed(1)} MB
            </div>
          )}
        </div>

        <div style={{ marginBottom: 20 }}>
          <label
            style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer" }}
          >
            <input
              type="checkbox"
              checked={geocode}
              onChange={(e) => setGeocode(e.target.checked)}
            />
            Geocode addresses (requires Geocodio API key — adds lat/lon and
            district verification)
          </label>
        </div>

        <button
          type="submit"
          disabled={!file || uploading}
          style={{
            padding: "10px 24px",
            background: uploading ? "#888" : "#4361ee",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            fontSize: 14,
            fontWeight: 600,
            cursor: uploading ? "default" : "pointer",
          }}
        >
          {uploading ? "Importing... (this may take a few minutes)" : "Import"}
        </button>
      </form>

      {error && (
        <div
          style={{
            marginTop: 16,
            background: "#fee",
            color: "#c00",
            padding: "12px 16px",
            borderRadius: 8,
            fontSize: 14,
            maxWidth: 500,
          }}
        >
          {error}
        </div>
      )}

      {result && (
        <div
          style={{
            marginTop: 16,
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            padding: "16px 20px",
            borderRadius: 8,
            maxWidth: 500,
          }}
        >
          <h3 style={{ margin: "0 0 12px", fontSize: 16, color: "#166534" }}>
            Import Complete
          </h3>
          <div style={{ fontSize: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
              <span>File</span>
              <strong>{result.file}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
              <span>Total records</span>
              <strong>{result.total?.toLocaleString()}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
              <span>Inserted</span>
              <strong>{result.inserted?.toLocaleString()}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
              <span>Updated</span>
              <strong>{result.updated?.toLocaleString()}</strong>
            </div>
            {result.errors > 0 && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "4px 0",
                  color: "#c00",
                }}
              >
                <span>Errors</span>
                <strong>{result.errors?.toLocaleString()}</strong>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
