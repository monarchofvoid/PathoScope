// User and Authentication Types
export enum UserRole {
  ICT_ADMIN = 'ict_admin',
  ICT_MEMBER = 'ict_member',
  VIEWER = 'viewer'
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  failed_login_attempts: number;
  locked_until?: string;
  mfa_enabled: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// Infection Case Types
export enum PathogenType {
  MDR_TB = 'MDR_TB',
  CRE = 'CRE',
  MRSA = 'MRSA',
  VRE = 'VRE',
  CANDIDA_AURIS = 'Candida_Auris',
  OTHER = 'Other'
}

export enum TestType {
  PCR = 'PCR',
  CULTURE = 'Culture',
  RAPID_MOLECULAR = 'Rapid_Molecular',
  ANTIGEN = 'Antigen'
}

export enum VerificationStatus {
  PENDING = 'pending',
  VERIFIED = 'verified',
  REJECTED = 'rejected'
}

export interface InfectionCase {
  id: string;
  case_number: string;
  patient_identifier: string;
  staff_identifier?: string;
  pathogen_type: PathogenType;
  test_type: TestType;
  specimen_collection_date: string;
  symptom_onset_date?: string;
  tek_lookback_days: number;
  verification_status: VerificationStatus;
  verified_by?: string;
  verified_at?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface InfectionCaseCreate {
  patient_identifier: string;
  staff_identifier?: string;
  pathogen_type: PathogenType;
  test_type: TestType;
  specimen_collection_date: string;
  symptom_onset_date?: string;
  tek_lookback_days?: number;
  notes?: string;
}

export interface InfectionCaseUpdate {
  pathogen_type?: PathogenType;
  test_type?: TestType;
  specimen_collection_date?: string;
  symptom_onset_date?: string;
  tek_lookback_days?: number;
  notes?: string;
}

// Verification Token Types
export enum TokenType {
  TEK_UPLOAD = 'tek_upload',
  FOLLOW_UP = 'follow_up'
}

export enum DeliveryMethod {
  HIS_SYSTEM = 'his_system',
  SMS = 'sms',
  EMAIL = 'email'
}

export interface VerificationToken {
  id: string;
  infection_case_id: string;
  token_value: string;
  token_type: TokenType;
  delivery_method: DeliveryMethod;
  delivery_address: string;
  issued_at: string;
  expires_at: string;
  used_at?: string;
  used_by?: string;
  is_active: boolean;
  created_by: string;
  infection_case: InfectionCase;
}

export interface TokenCreate {
  infection_case_id: string;
  token_type?: TokenType;
  delivery_method: DeliveryMethod;
  delivery_address: string;
  expires_hours?: number;
}

export interface TEKUpload {
  id: string;
  verification_token_id: string;
  upload_status: UploadStatus;
  tek_count: number;
  uploaded_at?: string;
  processed_at?: string;
  error_message?: string;
  retry_count: number;
  retention_expires_at: string;
}

export enum UploadStatus {
  PENDING = 'pending',
  COMPLETED = 'completed',
  FAILED = 'failed',
  EXPIRED = 'expired'
}

// Analytics and Dashboard Types
export enum AlertType {
  HIGH = 'high',
  MODERATE = 'moderate',
  LOW = 'low'
}

export enum ServiceStatus {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  DOWN = 'down'
}

export interface RiskAlert {
  id: string;
  alert_type: AlertType;
  exposure_count: number;
  location_identifier: string;
  time_window_start: string;
  time_window_end: string;
  detection_algorithm: string;
  confidence_score: number;
  acknowledged_by?: string;
  acknowledged_at?: string;
  notes?: string;
  created_at: string;
}

export interface KPIMetrics {
  total_alerts_24h: number;
  high_risk_alerts_24h: number;
  moderate_risk_alerts_24h: number;
  low_risk_alerts_24h: number;
  total_alerts_7d: number;
  total_alerts_30d: number;
  tek_upload_compliance_rate: number;
  average_upload_delay_hours: number;
  token_usage_rate: number;
  total_active_cases: number;
  new_cases_24h: number;
  new_cases_7d: number;
  new_cases_30d: number;
  pathogen_distribution: Record<string, number>;
  last_updated: string;
}

export interface SystemHealth {
  id: string;
  service_name: string;
  status: ServiceStatus;
  response_time_ms?: number;
  last_check: string;
  error_count: number;
  uptime_percentage: number;
  details?: Record<string, any>;
}

export interface ComplianceStats {
  total_cases: number;
  tokens_generated: number;
  tek_uploads_completed: number;
  tek_uploads_pending: number;
  tek_uploads_failed: number;
  compliance_rate: number;
  average_upload_delay_hours: number;
}

export interface AuditLog {
  id: string;
  user_id: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: string;
  ip_address?: string;
  timestamp: string;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Form Validation Types
export interface FormErrors {
  [key: string]: string[];
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Dashboard Component Props
export interface DashboardWidget {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
  };
  icon?: string;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

// Filter and Search Types
export interface CaseFilters {
  verification_status?: VerificationStatus;
  pathogen_type?: PathogenType;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export interface AlertFilters {
  hours_back?: number;
  acknowledged?: boolean;
  alert_type?: AlertType;
  location?: string;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: Array<{
    label: string;
    action: string;
  }>;
}