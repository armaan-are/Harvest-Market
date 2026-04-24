export default function SortBar({
  sortOrder,
  onSortChange,
  focusedKeyword,
  onClearKeyword,
}) {
  return (
    <div className="sort-bar">
      <label className="sort-bar__control">
        <span>Sort inventory</span>
        <select value={sortOrder} onChange={onSortChange}>
          <option value="default">Newest</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="popular">Most Purchased</option>
        </select>
      </label>

      {focusedKeyword ? (
        <div className="sort-bar__boost">
          <span>
            Boosting products related to <strong>{focusedKeyword}</strong>
          </span>
          <button className="button button--ghost" type="button" onClick={onClearKeyword}>
            Clear
          </button>
        </div>
      ) : null}
    </div>
  );
}
