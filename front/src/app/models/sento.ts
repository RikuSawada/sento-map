export interface Sento {
  id: number;
  name: string;
  address: string;
  lat: number;
  lng: number;
  phone: string | null;
  url: string | null;
  openHours: string | null;
  holiday: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface SentoListResponse {
  items: Sento[];
  total: number;
  page: number;
  perPage: number;
}
