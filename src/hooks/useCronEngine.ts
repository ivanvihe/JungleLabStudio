import { useCallback, useEffect, useRef } from 'react';
import { CronJob, CronJobRunResult } from '../types/automation';
import { cronMatches, validateCronExpression } from '../utils/cron';
import { runCommand } from '../utils/commandRunner';

interface UseCronEngineOptions {
  onJobRun: (jobId: string, result: CronJobRunResult) => void;
}

interface UseCronEngineReturn {
  runJobNow: (jobId: string) => Promise<void>;
}

export function useCronEngine(
  jobs: CronJob[],
  { onJobRun }: UseCronEngineOptions
): UseCronEngineReturn {
  const jobsRef = useRef<CronJob[]>(jobs);
  const lastExecutionRef = useRef<Record<string, string>>({});

  useEffect(() => {
    jobsRef.current = jobs;
  }, [jobs]);

  const executeJob = useCallback(
    async (job: CronJob, trigger: CronJobRunResult['trigger']) => {
      const timestamp = new Date().toISOString();
      const result = await runCommand(job.command, {
        cwd: job.workingDirectory
      });

      onJobRun(job.id, {
        ranAt: timestamp,
        success: result.success,
        stdout: result.stdout,
        stderr: result.stderr,
        code: result.code,
        trigger,
        errorMessage: result.errorMessage
      });
    },
    [onJobRun]
  );

  const checkJobs = useCallback(() => {
    const now = new Date();
    const minuteKey = now.toISOString().slice(0, 16);

    for (const job of jobsRef.current) {
      if (!job.enabled) {
        continue;
      }

      if (validateCronExpression(job.cronExpression)) {
        continue;
      }

      if (!cronMatches(now, job.cronExpression)) {
        continue;
      }

      if (lastExecutionRef.current[job.id] === minuteKey) {
        continue;
      }

      lastExecutionRef.current[job.id] = minuteKey;
      executeJob(job, 'schedule');
    }
  }, [executeJob]);

  useEffect(() => {
    checkJobs();
    const interval = window.setInterval(checkJobs, 30_000);
    return () => {
      window.clearInterval(interval);
    };
  }, [checkJobs]);

  const runJobNow = useCallback(
    async (jobId: string) => {
      const job = jobsRef.current.find((item) => item.id === jobId);
      if (!job) {
        return;
      }
      await executeJob(job, 'manual');
    },
    [executeJob]
  );

  return { runJobNow };
}
