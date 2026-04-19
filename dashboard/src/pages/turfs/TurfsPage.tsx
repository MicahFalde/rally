import { useEffect, useState } from "react";
import api from "../../api/client";
import type { Turf, CampaignMember } from "../../api/types";
import { useCampaign } from "../../context/CampaignContext";

export default function TurfsPage() {
  const { activeCampaign } = useCampaign();
  const [turfs, setTurfs] = useState<Turf[]>([]);
  const [members, setMembers] = useState<CampaignMember[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    if (!activeCampaign) return;
    setLoading(true);
    try {
      const [turfsRes, membersRes] = await Promise.all([
        api.get(`/campaigns/${activeCampaign.id}/turfs`),
        api.get(`/campaigns/${activeCampaign.id}/members`),
      ]);
      setTurfs(turfsRes.data);
      setMembers(membersRes.data);
    } finally {
      setLoading(false);
    }
  };

  const assignTurf = async (turfId: string, volunteerId: string) => {
    if (!activeCampaign) return;
    await api.post(`/campaigns/${activeCampaign.id}/turfs/${turfId}/assign`, {
      volunteer_id: volunteerId,
    });
    refresh();
  };

  useEffect(() => {
    refresh();
  }, [activeCampaign]);

  if (!activeCampaign) return <div>Select a campaign first.</div>;

  const getMemberName = (userId: string | null) => {
    if (!userId) return "Unassigned";
    const m = members.find((m) => m.user_id === userId);
    return m?.user?.full_name || userId.slice(0, 8);
  };

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
        <h2 style={{ margin: 0, fontSize: 22 }}>Turfs</h2>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : turfs.length === 0 ? (
        <div
          style={{
            background: "#fff",
            borderRadius: 8,
            padding: 40,
            textAlign: "center",
          }}
        >
          <h3 style={{ margin: "0 0 8px" }}>No turfs yet</h3>
          <p style={{ color: "#888", margin: 0, fontSize: 14 }}>
            Go to the Voters page, build a target list, then create turfs from
            selected voters.
          </p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: 16,
          }}
        >
          {turfs.map((turf) => {
            const progress =
              turf.total_doors > 0
                ? (turf.doors_knocked / turf.total_doors) * 100
                : 0;
            const contactRate =
              turf.doors_knocked > 0
                ? (turf.contacts_made / turf.doors_knocked) * 100
                : 0;

            return (
              <div
                key={turf.id}
                style={{
                  background: "#fff",
                  borderRadius: 8,
                  padding: 20,
                  border: turf.completed_at
                    ? "2px solid #22c55e"
                    : "1px solid #eee",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "start",
                  }}
                >
                  <h3 style={{ margin: 0, fontSize: 16 }}>{turf.name}</h3>
                  {turf.completed_at && (
                    <span
                      style={{
                        background: "#dcfce7",
                        color: "#166534",
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 600,
                      }}
                    >
                      Complete
                    </span>
                  )}
                </div>

                {turf.description && (
                  <p style={{ margin: "4px 0 0", fontSize: 13, color: "#888" }}>
                    {turf.description}
                  </p>
                )}

                {/* Progress bar */}
                <div
                  style={{
                    marginTop: 16,
                    height: 6,
                    background: "#eee",
                    borderRadius: 3,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${progress}%`,
                      background: "#4361ee",
                      borderRadius: 3,
                    }}
                  />
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginTop: 12,
                    fontSize: 13,
                    color: "#666",
                  }}
                >
                  <span>
                    {turf.doors_knocked}/{turf.total_doors} doors
                  </span>
                  <span>{contactRate.toFixed(0)}% contact rate</span>
                </div>

                {/* Assignment */}
                <div
                  style={{
                    marginTop: 12,
                    paddingTop: 12,
                    borderTop: "1px solid #eee",
                    fontSize: 13,
                  }}
                >
                  <label style={{ color: "#888", fontSize: 11 }}>
                    Assigned to
                  </label>
                  <select
                    value={turf.assigned_to_id || ""}
                    onChange={(e) => assignTurf(turf.id, e.target.value)}
                    style={{
                      width: "100%",
                      marginTop: 4,
                      padding: "6px 8px",
                      border: "1px solid #ddd",
                      borderRadius: 4,
                      fontSize: 13,
                    }}
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => (
                      <option key={m.user_id} value={m.user_id}>
                        {m.user?.full_name || m.user_id.slice(0, 8)} (
                        {m.role})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
