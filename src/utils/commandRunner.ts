export interface CommandRunOptions {
  cwd?: string;
}

export interface CommandRunResult {
  success: boolean;
  stdout: string;
  stderr: string;
  code: number;
  executedCommand: string;
  simulated: boolean;
  errorMessage?: string;
}

function splitCommandLine(command: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  let quoteChar: '"' | "'" | null = null;
  let escapeNext = false;

  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];

    if (escapeNext) {
      current += char;
      escapeNext = false;
      continue;
    }

    if (char === '\\') {
      escapeNext = true;
      continue;
    }

    if (char === '"' || char === "'") {
      if (!inQuotes) {
        inQuotes = true;
        quoteChar = char as '"' | "'";
        continue;
      }
      if (quoteChar === char) {
        inQuotes = false;
        quoteChar = null;
        continue;
      }
    }

    if (!inQuotes && /\s/.test(char)) {
      if (current) {
        result.push(current);
        current = '';
      }
      continue;
    }

    current += char;
  }

  if (current) {
    result.push(current);
  }

  return result;
}

export async function runCommand(
  command: string,
  options: CommandRunOptions = {}
): Promise<CommandRunResult> {
  const trimmed = command.trim();
  if (!trimmed) {
    return {
      success: false,
      stdout: '',
      stderr: 'Empty command',
      code: -1,
      executedCommand: '',
      simulated: true,
      errorMessage: 'Empty command'
    };
  }

  const args = splitCommandLine(trimmed);
  if (args.length === 0) {
    return {
      success: false,
      stdout: '',
      stderr: 'Unable to parse command',
      code: -1,
      executedCommand: trimmed,
      simulated: true,
      errorMessage: 'Unable to parse command'
    };
  }

  const [binary, ...rest] = args;
  const hasTauri = typeof window !== 'undefined' && Boolean((window as any).__TAURI__);

  if (hasTauri) {
    try {
      const shellModule = await import('@tauri-apps/api/shell');
      const commandInstance = new shellModule.Command(binary, rest, {
        cwd: options.cwd
      });
      const result = await commandInstance.execute();

      return {
        success: result.code === 0,
        stdout: result.stdout,
        stderr: result.stderr,
        code: result.code,
        executedCommand: trimmed,
        simulated: false,
        errorMessage:
          result.code === 0 ? undefined : result.stderr || 'Command returned a non-zero exit code'
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return {
        success: false,
        stdout: '',
        stderr: message,
        code: -1,
        executedCommand: trimmed,
        simulated: false,
        errorMessage: message
      };
    }
  }

  return {
    success: true,
    stdout: `Simulated execution: ${trimmed}`,
    stderr: '',
    code: 0,
    executedCommand: trimmed,
    simulated: true
  };
}
