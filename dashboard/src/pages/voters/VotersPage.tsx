import { useEffect, useState } from "react";
import api from "../../api/client";
import type { Voter, VoterFilters } from "../../api/types";
import { useCampaign } from "../../context/CampaignContext";

const PARTIES: Record<string, string> = {
  D: "Democrat",
  R: "Republican",
  L: "Libertarian",
  G: "Green",
  I: "Independent",
  O: "Other",
};

export default function VotersPage() {
  const { activeCampaign } = useCampaign();
  const [voters, setVoters] = useState<Voter[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [adding, setAdding] = useState(false);

  // Filters
  const [district, setDistrict] = useState("");
  const [precinct, setPrecinct] = useState("");
  const [party, setParty] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [status, setStatus] = useState("active");
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const search = async (newOffset = 0) => {
    if (!activeCampaign) return;
    setLoading(true);
    setOffset(newOffset);

    const params: Record<string, string | number> = {
      limit,
      offset: newOffset,
      voter_status: status,
    };
    if (district) params.state_house_district = district;
    if (precinct) params.precinct = precinct;
    if (party) params.party = party;
    if (zipCode) params.zip_code = zipCode;

    try {
      const res = await api.get(`/campaigns/${activeCampaign.id}/voters`, {
        params,
      });
      setVoters(res.data);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selected.size === voters.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(voters.map((v) => v.id)));
    }
  };

  const addToUniverse = async () => {
    if (!activeCampaign || selected.size === 0) return;
    setAdding(true);
    try {
      const res = await api.post(
        `/campaigns/${activeCampaign.id}/voters/target`,
        Array.from(selected)
      );
      alert(`Added ${res.data.added} voters to target universe`);
      setSelected(new Set());
    } finally {
      setAdding(false);
    }
  };

  const addByFilter = async () => {
    if (!activeCampaign) return;
    setAdding(true);
    try {
      const filters: VoterFilters = { voter_status: status };
      if (district) filters.state_house_district = district;
      if (precinct) filters.precinct = precinct;
      if (party) filters.party = party;
      if (zipCode) filters.zip_code = zipCode;

      const res = await api.post(
        `/campaigns/${activeCampaign.id}/voters/target/filter`,
        filters
      );
      alert(
        `Added ${res.data.added} voters to target universe (${res.data.total_matched} matched)`
      );
    } finally {
      setAdding(false);
    }
  };

  useEffect(() => {
    if (activeCampaign) search();
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
        <h2 style={{ margin: 0, fontSize: 22 }}>Voter File</h2>
        <div style={{ display: "flex", gap: 8 }}>
          {selected.size > 0 && (
            <button
              onClick={addToUniverse}
              disabled={adding}
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
              Add {selected.size} to universe
            </button>
          )}
          <button
            onClick={addByFilter}
            disabled={adding}
            style={{
              padding: "8px 16px",
              background: "#22c55e",
              color: "#fff",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 13,
            }}
          >
            Add all matching filters
          </button>
        </div>
      </div>

      {/* Filters */}
      <div
        style={{
          background: "#fff",
          borderRadius: 8,
          padding: 16,
          marginBottom: 16,
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          alignItems: "end",
        }}
      >
        <div>
          <label style={{ display: "block", fontSize: 11, color: "#888", marginBottom: 2 }}>
            House District
          </label>
          <input
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            placeholder="OH-HD-67"
            style={{ padding: "6px 8px", border: "1px solid #ddd", borderRadius: 4, width: 120, fontSize: 13 }}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: 11, color: "#888", marginBottom: 2 }}>
            Precinct
          </label>
          <input
            value={precinct}
            onChange={(e) => setPrecinct(e.target.value)}
            placeholder="Precinct name"
            style={{ padding: "6px 8px", border: "1px solid #ddd", borderRadius: 4, width: 150, fontSize: 13 }}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: 11, color: "#888", marginBottom: 2 }}>
            Party
          </label>
          <select
            value={party}
            onChange={(e) => setParty(e.target.value)}
            style={{ padding: "6px 8px", border: "1px solid #ddd", borderRadius: 4, fontSize: 13 }}
          >
            <option value="">All</option>
            <option value="D">Democrat</option>
            <option value="R">Republican</option>
            <option value="I">Independent</option>
            <option value="L">Libertarian</option>
            <option value="G">Green</option>
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 11, color: "#888", marginBottom: 2 }}>
            ZIP
          </label>
          <input
            value={zipCode}
            onChange={(e) => setZipCode(e.target.value)}
            placeholder="44805"
            style={{ padding: "6px 8px", border: "1px solid #ddd", borderRadius: 4, width: 80, fontSize: 13 }}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: 11, color: "#888", marginBottom: 2 }}>
            Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            style={{ padding: "6px 8px", border: "1px solid #ddd", borderRadius: 4, fontSize: 13 }}
          >
            <option value="active">Active</option>
            <option value="confirmation">Confirmation</option>
          </select>
        </div>
        <button
          onClick={() => search(0)}
          style={{
            padding: "6px 16px",
            background: "#4361ee",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            fontSize: 13,
          }}
        >
          Search
        </button>
      </div>

      {/* Results table */}
      <div style={{ background: "#fff", borderRadius: 8, overflow: "hidden" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 13,
          }}
        >
          <thead>
            <tr style={{ background: "#f9f9f9", textAlign: "left" }}>
              <th style={{ padding: "10px 12px", width: 32 }}>
                <input
                  type="checkbox"
                  checked={selected.size === voters.length && voters.length > 0}
                  onChange={selectAll}
                />
              </th>
              <th style={{ padding: "10px 12px" }}>Name</th>
              <th style={{ padding: "10px 12px" }}>Address</th>
              <th style={{ padding: "10px 12px" }}>City</th>
              <th style={{ padding: "10px 12px" }}>ZIP</th>
              <th style={{ padding: "10px 12px" }}>Party</th>
              <th style={{ padding: "10px 12px" }}>Precinct</th>
              <th style={{ padding: "10px 12px" }}>District</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ padding: 20, textAlign: "center" }}>
                  Loading...
                </td>
              </tr>
            ) : voters.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: 20, textAlign: "center", color: "#888" }}>
                  No voters found. Adjust filters and search.
                </td>
              </tr>
            ) : (
              voters.map((v) => (
                <tr
                  key={v.id}
                  style={{
                    borderTop: "1px solid #eee",
                    background: selected.has(v.id) ? "#f0f4ff" : "transparent",
                  }}
                >
                  <td style={{ padding: "8px 12px" }}>
                    <input
                      type="checkbox"
                      checked={selected.has(v.id)}
                      onChange={() => toggleSelect(v.id)}
                    />
                  </td>
                  <td style={{ padding: "8px 12px", fontWeight: 500 }}>
                    {v.first_name} {v.last_name}
                  </td>
                  <td style={{ padding: "8px 12px" }}>{v.address_line1}</td>
                  <td style={{ padding: "8px 12px" }}>{v.city}</td>
                  <td style={{ padding: "8px 12px" }}>{v.zip_code}</td>
                  <td style={{ padding: "8px 12px" }}>
                    {v.party ? PARTIES[v.party] || v.party : "—"}
                  </td>
                  <td style={{ padding: "8px 12px", fontSize: 12 }}>
                    {v.precinct || "—"}
                  </td>
                  <td style={{ padding: "8px 12px", fontSize: 12 }}>
                    {v.state_house_district || "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "12px 16px",
            borderTop: "1px solid #eee",
            fontSize: 13,
          }}
        >
          <span style={{ color: "#888" }}>
            Showing {offset + 1}-{offset + voters.length}
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => search(Math.max(0, offset - limit))}
              disabled={offset === 0}
              style={{
                padding: "4px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
                background: "#fff",
                cursor: offset === 0 ? "default" : "pointer",
                opacity: offset === 0 ? 0.5 : 1,
              }}
            >
              Previous
            </button>
            <button
              onClick={() => search(offset + limit)}
              disabled={voters.length < limit}
              style={{
                padding: "4px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
                background: "#fff",
                cursor: voters.length < limit ? "default" : "pointer",
                opacity: voters.length < limit ? 0.5 : 1,
              }}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
