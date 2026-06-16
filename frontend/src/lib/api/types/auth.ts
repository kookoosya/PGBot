export interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  phone?: string | null;
  role: string;
  department_id: number | null;
  is_active: boolean;
  organization?: string | null;
  position?: string | null;
  verification_status?: string | null;
  created_at: string;
}

export interface VerificationRequest {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  phone: string | null;
  organization: string | null;
  position: string | null;
  role: string;
  verification_status: string;
  verification_note: string | null;
  created_at: string;
}
