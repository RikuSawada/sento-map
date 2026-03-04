export interface Review {
  id: number;
  sentoId: number;
  userId: number;
  username: string;
  rating: number;
  comment: string | null;
  createdAt: string;
}

export interface ReviewCreate {
  rating: number;
  comment?: string;
}
