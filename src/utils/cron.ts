const CRON_RANGES = [
  { min: 0, max: 59 },
  { min: 0, max: 23 },
  { min: 1, max: 31 },
  { min: 1, max: 12 },
  { min: 0, max: 6 }
] as const;

type CronFieldRange = (typeof CRON_RANGES)[number];

const WHITESPACE_REGEX = /\s+/;

function normalize(field: string): string {
  return field.trim();
}

function matchCronToken(
  token: string,
  value: number,
  range: CronFieldRange
): boolean {
  const normalized = token.trim();
  if (!normalized) {
    return false;
  }

  if (normalized === '*') {
    return true;
  }

  const [rangePart, stepPart] = normalized.split('/');
  const step = stepPart ? parseInt(stepPart, 10) : 1;
  if (Number.isNaN(step) || step <= 0) {
    return false;
  }

  let start = range.min;
  let end = range.max;

  if (rangePart && rangePart !== '*') {
    if (rangePart.includes('-')) {
      const [startStr, endStr] = rangePart.split('-');
      start = parseInt(startStr, 10);
      end = parseInt(endStr, 10);
      if (
        Number.isNaN(start) ||
        Number.isNaN(end) ||
        start < range.min ||
        end > range.max ||
        start > end
      ) {
        return false;
      }
    } else {
      const exact = parseInt(rangePart, 10);
      if (
        Number.isNaN(exact) ||
        exact < range.min ||
        exact > range.max
      ) {
        return false;
      }
      start = exact;
      end = exact;
    }
  }

  if (value < start || value > end) {
    return false;
  }

  if (!rangePart || rangePart === '*') {
    return ((value - range.min) % step) === 0;
  }

  return ((value - start) % step) === 0;
}

function matchCronField(
  field: string,
  value: number,
  range: CronFieldRange
): boolean {
  const normalized = normalize(field);
  if (!normalized) {
    return false;
  }

  return normalized
    .split(',')
    .some(token => matchCronToken(token, value, range));
}

function validateCronField(field: string, range: CronFieldRange): string | null {
  const normalized = normalize(field);
  if (!normalized) {
    return 'Field cannot be empty';
  }

  const tokens = normalized.split(',');
  if (tokens.length === 0) {
    return 'Field must contain at least one value';
  }

  for (const token of tokens) {
    const trimmed = token.trim();
    if (!trimmed) {
      return 'Invalid empty token';
    }

    const [rangePart, stepPart] = trimmed.split('/');
    if (stepPart) {
      const step = parseInt(stepPart, 10);
      if (Number.isNaN(step) || step <= 0) {
        return `Invalid step value "${stepPart}"`;
      }
    }

    if (!rangePart || rangePart === '*') {
      continue;
    }

    if (rangePart.includes('-')) {
      const [startStr, endStr] = rangePart.split('-');
      const start = parseInt(startStr, 10);
      const end = parseInt(endStr, 10);
      if (Number.isNaN(start) || Number.isNaN(end)) {
        return `Invalid range "${rangePart}"`;
      }
      if (start < range.min || end > range.max || start > end) {
        return `Range "${rangePart}" outside allowed values`;
      }
    } else {
      const exact = parseInt(rangePart, 10);
      if (Number.isNaN(exact)) {
        return `Invalid value "${rangePart}"`;
      }
      if (exact < range.min || exact > range.max) {
        return `Value "${rangePart}" out of range`;
      }
    }
  }

  return null;
}

export function validateCronExpression(expression: string): string | null {
  if (!expression || !expression.trim()) {
    return 'Cron expression cannot be empty';
  }

  const parts = expression.trim().split(WHITESPACE_REGEX).filter(Boolean);
  if (parts.length !== 5) {
    return 'Cron expression must have 5 fields (minute hour day month weekday)';
  }

  for (let i = 0; i < parts.length; i += 1) {
    const error = validateCronField(parts[i], CRON_RANGES[i]);
    if (error) {
      return error;
    }
  }

  return null;
}

export function cronMatches(date: Date, expression: string): boolean {
  const parts = expression.trim().split(WHITESPACE_REGEX).filter(Boolean);
  if (parts.length !== 5) {
    return false;
  }

  const minute = date.getMinutes();
  const hour = date.getHours();
  const dayOfMonth = date.getDate();
  const month = date.getMonth() + 1;
  const dayOfWeek = date.getDay();

  const minuteMatch = matchCronField(parts[0], minute, CRON_RANGES[0]);
  const hourMatch = matchCronField(parts[1], hour, CRON_RANGES[1]);
  const monthMatch = matchCronField(parts[3], month, CRON_RANGES[3]);
  const dayOfMonthMatch = matchCronField(parts[2], dayOfMonth, CRON_RANGES[2]);
  const dayOfWeekMatch = matchCronField(parts[4], dayOfWeek, CRON_RANGES[4]);

  const domWildcard = parts[2] === '*';
  const dowWildcard = parts[4] === '*';
  const dayMatch =
    (domWildcard && dowWildcard) ||
    (domWildcard && dayOfWeekMatch) ||
    (dowWildcard && dayOfMonthMatch) ||
    (dayOfMonthMatch && dayOfWeekMatch);

  return minuteMatch && hourMatch && monthMatch && dayMatch;
}

export function getNextRun(
  expression: string,
  fromDate: Date = new Date(),
  maxIterations = 60 * 24 * 31
): Date | null {
  if (validateCronExpression(expression)) {
    return null;
  }

  const start = new Date(fromDate.getTime());
  start.setSeconds(0, 0);
  start.setMinutes(start.getMinutes() + 1);

  const candidate = new Date(start.getTime());

  for (let i = 0; i < maxIterations; i += 1) {
    if (cronMatches(candidate, expression)) {
      return new Date(candidate.getTime());
    }
    candidate.setMinutes(candidate.getMinutes() + 1);
  }

  return null;
}
