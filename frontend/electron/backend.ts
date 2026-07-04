/** Manages the local FastAPI backend process: spawn, health-check, auto-restart. */
import { spawn, type ChildProcess } from 'node:child_process';
import { get } from 'node:http';
import { join } from 'node:path';

import { app } from 'electron';

export type BackendPhase = 'starting' | 'ready' | 'stopped' | 'error';

export interface BackendStatus {
  phase: BackendPhase;
  detail?: string;
}

const HEALTH_URL = 'http://127.0.0.1:8000/api/health';
const MAX_RESTARTS = 5;
const HEALTH_TIMEOUT_MS = 30_000;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function checkHealth(): Promise<boolean> {
  return new Promise((resolve) => {
    const req = get(HEALTH_URL, (res) => {
      res.resume();
      resolve((res.statusCode ?? 500) < 400);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(2000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

export class BackendManager {
  private child: ChildProcess | null = null;
  private status: BackendStatus = { phase: 'stopped' };
  private restarts = 0;
  private stopping = false;

  constructor(private readonly onStatus: (status: BackendStatus) => void) {}

  getStatus(): BackendStatus {
    return this.status;
  }

  private update(status: BackendStatus): void {
    this.status = status;
    this.onStatus(status);
  }

  private backendCwd(): string {
    return app.isPackaged
      ? join(process.resourcesPath, 'backend')
      : join(app.getAppPath(), '..', 'backend');
  }

  /**
   * Choose how to launch the backend.
   *
   * Packaged builds run the self-contained PyInstaller executable and are told
   * (via ``EXO_*`` env) to store data under the OS ``userData`` directory, which
   * is writable (unlike the read-only install/resources directory). In a
   * non-packaged run the developer's Python + uvicorn is used.
   */
  private launchSpec(): { command: string; args: string[]; env: NodeJS.ProcessEnv } {
    if (app.isPackaged) {
      const executable = process.platform === 'win32' ? 'exo-backend.exe' : 'exo-backend';
      const userData = app.getPath('userData');
      return {
        command: join(process.resourcesPath, 'backend', executable),
        args: [],
        env: {
          ...process.env,
          EXO_ENV: 'production',
          EXO_HOST: '127.0.0.1',
          EXO_PORT: '8000',
          EXO_DB_PATH: join(userData, 'database', 'exo.db'),
          EXO_LOG_DIR: join(userData, 'logs'),
          EXO_PLUGINS_DIR: join(process.resourcesPath, 'plugins'),
        },
      };
    }
    return {
      command: process.env.EXO_PYTHON ?? 'python',
      args: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
      env: { ...process.env },
    };
  }

  start(): void {
    this.stopping = false;
    this.spawnProcess();
  }

  private spawnProcess(): void {
    this.update({ phase: 'starting' });
    const { command, args, env } = this.launchSpec();
    const child = spawn(command, args, { cwd: this.backendCwd(), env });
    this.child = child;
    child.on('error', (error) => this.update({ phase: 'error', detail: error.message }));
    child.on('exit', (code) => this.handleExit(code));
    void this.waitForHealth();
  }

  private handleExit(code: number | null): void {
    this.child = null;
    if (this.stopping) {
      this.update({ phase: 'stopped' });
      return;
    }
    if (this.restarts >= MAX_RESTARTS) {
      this.update({
        phase: 'error',
        detail: `Backend exited (code ${code ?? 'unknown'}) and exceeded the restart limit.`,
      });
      return;
    }
    this.restarts += 1;
    this.update({
      phase: 'error',
      detail: `Backend exited (code ${code ?? 'unknown'}); restarting (${this.restarts}/${MAX_RESTARTS})…`,
    });
    setTimeout(() => {
      if (!this.stopping) {
        this.spawnProcess();
      }
    }, 1000 * this.restarts);
  }

  private async waitForHealth(): Promise<void> {
    const deadline = Date.now() + HEALTH_TIMEOUT_MS;
    while (Date.now() < deadline && !this.stopping) {
      if (await checkHealth()) {
        this.restarts = 0;
        this.update({ phase: 'ready' });
        return;
      }
      await delay(500);
    }
    if (!this.stopping && this.status.phase !== 'ready') {
      this.update({ phase: 'error', detail: 'Backend did not become healthy in time.' });
    }
  }

  stop(): void {
    this.stopping = true;
    if (this.child) {
      this.child.kill();
      this.child = null;
    }
    this.update({ phase: 'stopped' });
  }
}
