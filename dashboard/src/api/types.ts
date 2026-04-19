export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  platform_role: string;
  zip_code: string | null;
  discoverable: boolean;
  total_doors_knocked: number;
  total_contacts_made: number;
  total_campaigns: number;
  created_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  state: string;
  district: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CampaignMember {
  id: string;
  user_id: string;
  campaign_id: string;
  role: string;
  is_active: boolean;
  doors_knocked: number;
  contacts_made: number;
  hours_volunteered: number;
  user?: User;
}

export interface Voter {
  id: string;
  state_voter_id: string;
  state: string;
  first_name: string;
  last_name: string;
  address_line1: string;
  city: string;
  zip_code: string;
  county: string | null;
  party: string | null;
  state_house_district: string | null;
  precinct: string | null;
  turnout_score: number | null;
  partisanship_score: number | null;
  persuadability_score: number | null;
}

export interface Turf {
  id: string;
  campaign_id: string;
  name: string;
  description: string | null;
  total_doors: number;
  doors_knocked: number;
  contacts_made: number;
  assigned_to_id: string | null;
  assigned_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface SurveyQuestion {
  id: string;
  question_text: string;
  question_key: string;
  order: number;
  options: { value: string; label: string }[];
}

export interface Survey {
  id: string;
  campaign_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  questions: SurveyQuestion[];
}

export interface CampaignStats {
  total_voters_in_universe: number;
  total_doors_knocked: number;
  total_contacts_made: number;
  contact_rate: number;
  support_breakdown: Record<string, number>;
  total_volunteers: number;
  total_turfs: number;
  turfs_completed: number;
}

export interface VoterFilters {
  state_house_district?: string;
  precinct?: string;
  party?: string;
  min_turnout_score?: number;
  max_turnout_score?: number;
  min_persuadability_score?: number;
  voter_status?: string;
  zip_code?: string;
  county?: string;
  limit?: number;
  offset?: number;
}
