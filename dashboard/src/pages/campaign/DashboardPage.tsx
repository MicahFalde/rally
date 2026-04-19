import { useEffect, useState } from "react";
import api from "../../api/client";
import type { CampaignStats } from "../../api/types";
import { useCampaign } from "../../context/CampaignContext";

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div
      style={{
        background: "#fff",
        borderRadius: 8,
        padding: "20px 24px",
        flex: 1,
        minWidth: 180,
      }}
    >
      <div style={{ fontSize: 12, color: "#888", textTransform: "uppercase" }}>
        {label}
      </div>
      <div style={{ fontSize: 32, fontWeight: 700, margin: "4px 0" }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: "#888" }}>{sub}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const { activeCampaign } = useCampaign();
  const [stats, setStats] = useState<CampaignStats | null>(null);

  useEffect(() => {
    if (!activeCampaign) return;
    api
      .get(`/campaigns/${activeCampaign.id}/stats`)
      .then((res) => setStats(res.data));
  }, [activeCampaign]);

  if (!activeCampaign) {
    return (
      <div>
        <h2>No campaign selected</h2>
        <p>Create or join a campaign to get started.</p>
      </div>
    );
  }

  if (!stats) return <div>Loading...</div>;

  const supportLabels: Record<string, string> = {
    strong_support: "Strong Support",
    lean_support: "Lean Support",
    undecided: "Undecided",
    lean_oppose: "Lean Oppose",
    strong_oppose: "Strong Oppose",
  };

  const supportColors: Record<string, string> = {
    strong_support: "#22c55e",
    lean_support: "#86efac",
    undecided: "#fbbf24",
    lean_oppose: "#fb923c",
    strong_oppose: "#ef4444",
  };

  const totalSupport = Object.values(stats.support_breakdown).reduce(
    (a, b) => a + b,
    0
  );

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 22 }}>{activeCampaign.name}</h2>
        <p style={{ margin: "4px 0 0", color: "#666", fontSize: 14 }}>
          {activeCampaign.district} — {activeCampaign.state}
        </p>
      </div>

      {/* Stats cards */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
        <StatCard
          label="Target Universe"
          value={stats.total_voters_in_universe.toLocaleString()}
          sub="voters to contact"
        />
        <StatCard
          label="Doors Knocked"
          value={stats.total_doors_knocked.toLocaleString()}
          sub={`${((stats.total_doors_knocked / Math.max(stats.total_voters_in_universe, 1)) * 100).toFixed(1)}% of universe`}
        />
        <StatCard
          label="Contact Rate"
          value={`${(stats.contact_rate * 100).toFixed(1)}%`}
          sub={`${stats.total_contacts_made} conversations`}
        />
        <StatCard
          label="Volunteers"
          value={stats.total_volunteers}
        />
        <StatCard
          label="Turfs"
          value={`${stats.turfs_completed}/${stats.total_turfs}`}
          sub="completed"
        />
      </div>

      {/* Support breakdown */}
      {totalSupport > 0 && (
        <div style={{ background: "#fff", borderRadius: 8, padding: 24 }}>
          <h3 style={{ margin: "0 0 16px", fontSize: 16 }}>
            Voter ID Breakdown
          </h3>

          {/* Stacked bar */}
          <div
            style={{
              display: "flex",
              height: 32,
              borderRadius: 4,
              overflow: "hidden",
              marginBottom: 16,
            }}
          >
            {Object.entries(stats.support_breakdown).map(([level, count]) => (
              <div
                key={level}
                style={{
                  width: `${(count / totalSupport) * 100}%`,
                  background: supportColors[level] || "#ccc",
                }}
                title={`${supportLabels[level] || level}: ${count}`}
              />
            ))}
          </div>

          {/* Legend */}
          <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
            {Object.entries(stats.support_breakdown).map(([level, count]) => (
              <div
                key={level}
                style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}
              >
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: 2,
                    background: supportColors[level] || "#ccc",
                  }}
                />
                {supportLabels[level] || level}: {count}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
