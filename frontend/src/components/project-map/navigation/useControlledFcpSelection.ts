import { useCallback, useState } from 'react';

export function useControlledFcpSelection({
  controlledSelectedFcpId,
  onSelectedFcpIdChange,
}: {
  controlledSelectedFcpId?: string | null;
  onSelectedFcpIdChange?: (id: string | null) => void;
}) {
  const [internalSelectedFcpId, setInternalSelectedFcpId] = useState<string | null>(null);

  const isControlled = onSelectedFcpIdChange != null;
  const selectedFcpId = isControlled
    ? (controlledSelectedFcpId ?? null)
    : internalSelectedFcpId;

  const updateSelectedFcpId = useCallback(
    (id: string | null) => {
      if (isControlled) {
        onSelectedFcpIdChange!(id);
      } else {
        setInternalSelectedFcpId(id);
      }
    },
    [isControlled, onSelectedFcpIdChange],
  );

  return {
    isControlled,
    selectedFcpId,
    updateSelectedFcpId,
  };
}
