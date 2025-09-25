export interface ProjectConfig {
  id: string;
  name: string;
  localPath: string;
  repoUrl: string;
  defaultBranch: string;
  personalAccessToken?: string;
  autoSyncCron?: string;
  description?: string;
  lastSyncAt?: string;
  lastSyncStatus?: 'idle' | 'success' | 'error';
  lastSyncMessage?: string;
}

export interface ProjectValidationResult {
  success: boolean;
  message: string;
  defaultBranch?: string;
  stars?: number;
  repoExists?: boolean;
}
