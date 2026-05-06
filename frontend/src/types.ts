export interface Project {
  id: number;
  name: string;
  created_at: string;
  expiry_months: number;
}

export interface QuestionSummary {
  code: string;
  label: string;
  type: string;
}

export interface ProjectDetail {
  id: number;
  name: string;
  questions: QuestionSummary[];
  weight_variable: string | null;
  wave_variable: string | null;
}

export interface ChartData {
  type: 'bar' | 'line' | 'pie';
  question_label: string;
  base_label?: string;
  labels: string[];
  datasets: { label: string; data: number[] }[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chart?: ChartData | null;
  timestamp: Date;
}

export interface QueryResponse {
  response: string;
  chart: ChartData | null;
}

export interface HistoryEntry {
  id: number;
  question: string;
  response: string;
  chart: ChartData | null;
  created_at: string;
}
