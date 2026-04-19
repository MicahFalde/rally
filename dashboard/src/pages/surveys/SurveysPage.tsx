import { useEffect, useState } from "react";
import api from "../../api/client";
import type { Survey } from "../../api/types";
import { useCampaign } from "../../context/CampaignContext";

interface NewQuestion {
  question_text: string;
  question_key: string;
  order: number;
  options: { value: string; label: string }[];
}

const DEFAULT_SUPPORT_OPTIONS = [
  { value: "strong_support", label: "Strong Support" },
  { value: "lean_support", label: "Lean Support" },
  { value: "undecided", label: "Undecided" },
  { value: "lean_oppose", label: "Lean Oppose" },
  { value: "strong_oppose", label: "Strong Oppose" },
];

export default function SurveysPage() {
  const { activeCampaign } = useCampaign();
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  // Create form
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [questions, setQuestions] = useState<NewQuestion[]>([
    {
      question_text: "Do you support our candidate?",
      question_key: "support",
      order: 1,
      options: DEFAULT_SUPPORT_OPTIONS,
    },
  ]);

  const refresh = async () => {
    if (!activeCampaign) return;
    setLoading(true);
    try {
      const res = await api.get(`/campaigns/${activeCampaign.id}/surveys`);
      setSurveys(res.data);
    } finally {
      setLoading(false);
    }
  };

  const createSurvey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCampaign) return;
    await api.post(`/campaigns/${activeCampaign.id}/surveys`, {
      name,
      description: description || null,
      questions,
    });
    setName("");
    setDescription("");
    setQuestions([
      {
        question_text: "Do you support our candidate?",
        question_key: "support",
        order: 1,
        options: DEFAULT_SUPPORT_OPTIONS,
      },
    ]);
    setShowCreate(false);
    refresh();
  };

  const addQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: "",
        question_key: `q${questions.length + 1}`,
        order: questions.length + 1,
        options: [
          { value: "yes", label: "Yes" },
          { value: "no", label: "No" },
        ],
      },
    ]);
  };

  const updateQuestion = (idx: number, field: string, value: string) => {
    const updated = [...questions];
    (updated[idx] as any)[field] = value;
    setQuestions(updated);
  };

  useEffect(() => {
    refresh();
  }, [activeCampaign]);

  if (!activeCampaign) return <div>Select a campaign first.</div>;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <h2 style={{ margin: 0, fontSize: 22 }}>Surveys</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          style={{
            padding: "8px 16px",
            background: "#4361ee",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            fontSize: 13,
          }}
        >
          {showCreate ? "Cancel" : "New Survey"}
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <form
          onSubmit={createSurvey}
          style={{
            background: "#fff",
            borderRadius: 8,
            padding: 24,
            marginBottom: 16,
          }}
        >
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
              Survey Name
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Door Knock — Persuasion"
              style={{
                width: "100%",
                padding: "8px 10px",
                border: "1px solid #ddd",
                borderRadius: 4,
                fontSize: 14,
                boxSizing: "border-box",
              }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
              Description (optional)
            </label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Script for first-pass door knock canvassing"
              style={{
                width: "100%",
                padding: "8px 10px",
                border: "1px solid #ddd",
                borderRadius: 4,
                fontSize: 14,
                boxSizing: "border-box",
              }}
            />
          </div>

          <h4 style={{ margin: "0 0 12px", fontSize: 14 }}>Questions</h4>
          {questions.map((q, idx) => (
            <div
              key={idx}
              style={{
                background: "#f9f9f9",
                borderRadius: 6,
                padding: 16,
                marginBottom: 12,
              }}
            >
              <div style={{ display: "flex", gap: 12, marginBottom: 8 }}>
                <input
                  value={q.question_text}
                  onChange={(e) =>
                    updateQuestion(idx, "question_text", e.target.value)
                  }
                  placeholder="Question text"
                  required
                  style={{
                    flex: 1,
                    padding: "6px 8px",
                    border: "1px solid #ddd",
                    borderRadius: 4,
                    fontSize: 13,
                  }}
                />
                <input
                  value={q.question_key}
                  onChange={(e) =>
                    updateQuestion(idx, "question_key", e.target.value)
                  }
                  placeholder="Key"
                  required
                  style={{
                    width: 100,
                    padding: "6px 8px",
                    border: "1px solid #ddd",
                    borderRadius: 4,
                    fontSize: 13,
                  }}
                />
              </div>
              <div style={{ fontSize: 12, color: "#888" }}>
                Options:{" "}
                {q.options.map((o) => o.label).join(", ")}
              </div>
            </div>
          ))}
          <button
            type="button"
            onClick={addQuestion}
            style={{
              padding: "6px 12px",
              background: "#eee",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 12,
              marginBottom: 16,
            }}
          >
            + Add question
          </button>

          <div>
            <button
              type="submit"
              style={{
                padding: "8px 20px",
                background: "#4361ee",
                color: "#fff",
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              Create Survey
            </button>
          </div>
        </form>
      )}

      {/* Survey list */}
      {loading ? (
        <div>Loading...</div>
      ) : surveys.length === 0 && !showCreate ? (
        <div
          style={{
            background: "#fff",
            borderRadius: 8,
            padding: 40,
            textAlign: "center",
          }}
        >
          <h3 style={{ margin: "0 0 8px" }}>No surveys yet</h3>
          <p style={{ color: "#888", margin: 0, fontSize: 14 }}>
            Create a survey to define the questions volunteers ask at the door.
          </p>
        </div>
      ) : (
        surveys.map((s) => (
          <div
            key={s.id}
            style={{
              background: "#fff",
              borderRadius: 8,
              padding: 20,
              marginBottom: 12,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <h3 style={{ margin: 0, fontSize: 16 }}>{s.name}</h3>
              <span
                style={{
                  background: s.is_active ? "#dcfce7" : "#fee",
                  color: s.is_active ? "#166534" : "#c00",
                  padding: "2px 8px",
                  borderRadius: 4,
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                {s.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            {s.description && (
              <p style={{ margin: "4px 0 0", fontSize: 13, color: "#888" }}>
                {s.description}
              </p>
            )}
            <div style={{ marginTop: 12 }}>
              {s.questions.map((q) => (
                <div
                  key={q.id}
                  style={{
                    padding: "8px 0",
                    borderTop: "1px solid #f0f0f0",
                    fontSize: 13,
                  }}
                >
                  <strong>{q.question_text}</strong>
                  <div style={{ color: "#888", marginTop: 2 }}>
                    {q.options.map((o) => o.label).join(" / ")}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
