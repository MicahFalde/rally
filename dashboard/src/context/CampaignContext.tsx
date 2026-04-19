import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import api from "../api/client";
import type { Campaign } from "../api/types";
import { useAuth } from "./AuthContext";

interface CampaignContextType {
  campaigns: Campaign[];
  activeCampaign: Campaign | null;
  setActiveCampaign: (c: Campaign) => void;
  refreshCampaigns: () => Promise<void>;
}

const CampaignContext = createContext<CampaignContextType | null>(null);

export function CampaignProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [activeCampaign, setActiveCampaign] = useState<Campaign | null>(null);

  const refreshCampaigns = async () => {
    const res = await api.get("/campaigns");
    setCampaigns(res.data);
    if (res.data.length > 0 && !activeCampaign) {
      setActiveCampaign(res.data[0]);
    }
  };

  useEffect(() => {
    if (user) {
      refreshCampaigns();
    }
  }, [user]);

  return (
    <CampaignContext.Provider
      value={{ campaigns, activeCampaign, setActiveCampaign, refreshCampaigns }}
    >
      {children}
    </CampaignContext.Provider>
  );
}

export function useCampaign() {
  const ctx = useContext(CampaignContext);
  if (!ctx) throw new Error("useCampaign must be inside CampaignProvider");
  return ctx;
}
