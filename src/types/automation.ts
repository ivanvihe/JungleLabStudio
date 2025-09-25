export type CronJobSource = 'user' | 'project';

export interface CronJob {
  id: string;
  name: string;
  cronExpression: string;
  command: string;
  enabled: boolean;
  workingDirectory?: string;
  lastRunAt?: string;
  lastStatus?: 'success' | 'error';
  lastOutput?: string;
  lastError?: string;
  source?: CronJobSource;
  projectId?: string;
}

export interface CronJobRunResult {
  ranAt: string;
  success: boolean;
  stdout: string;
  stderr: string;
  code: number;
  trigger: 'schedule' | 'manual';
  errorMessage?: string;
}
