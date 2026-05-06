import axios from 'axios';
import type { Project, ProjectDetail, QueryResponse, HistoryEntry } from './types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 90000,
});

export const getProjects = () =>
  api.get<Project[]>('/projects/').then(r => r.data);

export const getProject = (id: number) =>
  api.get<ProjectDetail>(`/projects/${id}`).then(r => r.data);

export const queryProject = (id: number, question: string) =>
  api.post<QueryResponse>(`/projects/${id}/query`, { question }).then(r => r.data);

export const getHistory = (id: number) =>
  api.get<HistoryEntry[]>(`/projects/${id}/history`).then(r => r.data);
