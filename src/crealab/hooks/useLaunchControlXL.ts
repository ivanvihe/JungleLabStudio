import { useEffect, useState } from 'react';
import { SessionMidiController } from '../types/GeneratorTypes';
import { SessionMidiManager } from '../core/SessionMidiController';

/**
 * React hook that exposes the current state of the Launch Control XL
 * controller. It initializes the {@link SessionMidiManager}, detects the
 * controller and subscribes to subsequent updates.
 */
export function useLaunchControlXL() {
  const [controller, setController] = useState<SessionMidiController | null>(
    null
  );

  useEffect(() => {
    const manager = SessionMidiManager.getInstance();
    let unsubscribe: (() => void) | undefined;

    manager.initialize().then(() => {
      const ctrl = manager.detectLaunchControlXL();
      if (ctrl) {
        setController({ ...ctrl });
      }
      unsubscribe = manager.onUpdate(c => setController({ ...c }));
    });

    return () => {
      unsubscribe?.();
    };
  }, []);

  return controller;
}

export default useLaunchControlXL;
