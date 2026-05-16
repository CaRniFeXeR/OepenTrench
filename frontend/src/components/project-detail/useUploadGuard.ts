import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

export function useUploadGuard(
  uploadsBusy: boolean,
  onUploadsBusyChange?: (busy: boolean) => void,
) {
  const blocker = useBlocker(uploadsBusy);

  useEffect(() => {
    onUploadsBusyChange?.(uploadsBusy);
  }, [uploadsBusy, onUploadsBusyChange]);

  useEffect(() => {
    return () => onUploadsBusyChange?.(false);
  }, [onUploadsBusyChange]);

  useEffect(() => {
    if (!uploadsBusy) return;
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [uploadsBusy]);

  useEffect(() => {
    if (blocker.state !== 'blocked') return;
    const leave = window.confirm(
      'Uploads are still in progress. Leaving now may interrupt uploads. Leave anyway?',
    );
    if (leave) blocker.proceed();
    else blocker.reset();
  }, [blocker]);
}
