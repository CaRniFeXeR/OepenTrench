export function paginatePage<T>(
  items: T[],
  page: number,
  pageSize: number,
): { pageItems: T[]; totalPages: number; startIndex: number; endIndex: number } {
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, items.length);
  return {
    pageItems: items.slice(startIndex, endIndex),
    totalPages,
    startIndex,
    endIndex,
  };
}
