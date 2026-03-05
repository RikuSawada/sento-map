export interface Sento {
  id: number;
  name: string;
  address: string;
  lat: number | null;
  lng: number | null;
  phone: string | null;
  url: string | null;
  openHours: string | null;
  holiday: string | null;
  prefecture: string | null;
  region: string | null;
  sourceUrl: string | null;
  geocodedBy: string | null;
  facilityType: 'sento' | 'onsen' | 'super_sento' | null;
  createdAt: string;
  updatedAt: string;
}

export interface SentoListResponse {
  items: Sento[];
  total: number;
  page: number;
  perPage: number;
}
