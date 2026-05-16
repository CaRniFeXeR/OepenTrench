import type { FcpCoverageRead } from '../../api/client';
import { TrenchCoverageSection } from './TrenchCoverageSection';

export function TrenchCoverageOverview({
  routeReady,
  coverage,
  loading,
  calculating,
  error,
  selectedFcpId,
  onCalculate,
}: {
  routeReady: boolean;
  coverage: FcpCoverageRead | null;
  loading: boolean;
  calculating: boolean;
  error: string | null;
  selectedFcpId: string | null;
  onCalculate: () => void;
}) {
  return (
    <TrenchCoverageSection
      coverage={coverage}
      loading={loading}
      error={error}
      selectedFcpId={selectedFcpId}
      showCalculateButton
      calculating={calculating}
      routeReady={routeReady}
      onCalculate={onCalculate}
    />
  );
}
