/**
 * Controls sorting and shows the "boosted" keyword when using similar products.
 */
export default function SortBar({
  sortOrder,
  onSortChange,
  focusedKeyword,
  onClearKeyword,
}) {
  return (
    <div
      style={{
        padding: "12px 16px",
        borderRadius: "10px",
        border: "1px solid #e5e7eb",
        marginBottom: "20px",
        backgroundColor: "rgba(255, 255, 255, 0.95)",
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: "12px",
      }}
    >
      <label>
        Sort by:
        <select
          value={sortOrder}
          onChange={onSortChange}
          style={{
            marginLeft: "8px",
            padding: "6px",
            borderRadius: "4px",
            border: "1px solid #d1d5db",
          }}
        >
          <option value="default">Default (Newest)</option>
          <option value="price_asc">Price: Low → High</option>
          <option value="price_desc">Price: High → Low</option>
          <option value="popular">Popularity (Most bought)</option>
        </select>
      </label>

      {focusedKeyword && (
        <div
          style={{
            fontSize: "12px",
            color: "#4b5563",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          Boosting products related to: <strong>{focusedKeyword}</strong>
          <button
            type="button"
            onClick={onClearKeyword}
            style={{
              padding: "2px 8px",
              borderRadius: "6px",
              border: "1px solid #d1d5db",
              backgroundColor: "#ffffff",
              cursor: "pointer",
              fontSize: "11px",
            }}
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
}