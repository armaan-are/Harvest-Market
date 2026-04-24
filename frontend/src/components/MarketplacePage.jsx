import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import CreateProductForm from "./CreateProductForm";
import ProductList from "./ProductList";
import SortBar from "./SortBar";

const categories = [
  { id: "all", label: "All Harvests" },
  { id: "produce", label: "Produce" },
  { id: "dairy", label: "Dairy" },
  { id: "meat", label: "Meat" },
  { id: "baked_goods", label: "Baked Goods" },
];

export default function MarketplacePage({
  currentUser,
  editTarget,
  featuredStats,
  focusKeyword,
  loadingProducts,
  onClearBoost,
  onCreateProduct,
  onDeleteProduct,
  onEditProduct,
  onFocusKeyword,
  onOpenMessages,
  onPurchase,
  onRequireAuth,
  onSaveEdit,
  onSearchChange,
  onSetCategory,
  onSetSortOrder,
  onSetZipFilter,
  products,
  savingEdit,
  savingProduct,
  searchTerm,
  selectedCategory,
  sortOrder,
  zipFilter,
}) {
  const isSeller = currentUser?.role === "seller";
  const [preferredFarm, setPreferredFarm] = useState("all");
  const [preferredCategory, setPreferredCategory] = useState("all");
  const location = useLocation();
  const navigate = useNavigate();
  const farmOptions = useMemo(() => {
    const farms = new Map();
    products.forEach((product) => {
      if (product.seller_id && product.farm_name) {
        farms.set(product.seller_id, {
          id: product.seller_id,
          name: product.farm_name,
          zip: product.zip_code,
        });
      }
    });
    return [...farms.values()].sort((left, right) => left.name.localeCompare(right.name));
  }, [products]);

  useEffect(() => {
    if (location.hash !== "#live-marketplace") {
      return;
    }

    document.getElementById("live-marketplace")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [location.hash]);

  return (
    <div className="market-page">
      <section className="editorial-market-tools" id="live-marketplace">
        <div className="inventory-section__header market-section-header">
          <div className="section-heading">
            <p className="eyebrow">Market</p>
            <h1>Shop local inventory.</h1>
            <p>Filter products, request pickup orders, message farms, and manage seller listings.</p>
          </div>
          <div className="inventory-section__filters">
            <label className="search-field">
              <span>Search</span>
              <input
                type="search"
                value={searchTerm}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder="Search inventory..."
              />
            </label>
            <label className="search-field">
              <span>Zip filter</span>
              <input
                type="text"
                value={zipFilter}
                onChange={(event) => onSetZipFilter(event.target.value)}
                placeholder="06268"
              />
            </label>
            <button
              className="button button--ghost market-clear"
              type="button"
              onClick={() => {
                onSearchChange("");
                onSetCategory("all");
                onSetZipFilter("");
                setPreferredFarm("all");
                setPreferredCategory("all");
                onClearBoost();
              }}
            >
              Clear
            </button>
          </div>
        </div>

        <div className="stats-row stats-row--tight">
          {featuredStats.map((stat) => (
            <article className="stat-card" key={stat.label}>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </article>
          ))}
        </div>

        <div className="category-row" role="tablist" aria-label="Product categories">
          {categories.map((category) => (
            <button
              key={category.id}
              type="button"
              className={
                selectedCategory === category.id
                  ? "chip-button chip-button--active"
                  : "chip-button"
              }
              onClick={() => onSetCategory(category.id)}
            >
              {category.label}
            </button>
          ))}
        </div>

        <div className="market-workspace">
          <aside className="market-control-panel">
            <SortBar
              sortOrder={sortOrder}
              onSortChange={(event) => onSetSortOrder(event.target.value)}
              focusedKeyword={focusKeyword}
              onClearKeyword={onClearBoost}
            />

            <section className="preference-panel">
              <div className="section-heading">
                <p className="eyebrow">Preference Survey</p>
                <h3>Personalize results</h3>
              </div>
              <label>
                Favorite category
                <select
                  value={preferredCategory}
                  onChange={(event) => setPreferredCategory(event.target.value)}
                >
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Preferred farm
                <select
                  value={preferredFarm}
                  onChange={(event) => setPreferredFarm(event.target.value)}
                >
                  <option value="all">Any farm</option>
                  {farmOptions.map((farm) => (
                    <option key={farm.id} value={farm.id}>
                      {farm.name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="button button--primary"
                type="button"
                onClick={() => {
                  if (!currentUser) {
                    onRequireAuth("Sign in to save marketplace preferences.");
                    return;
                  }
                  onSetCategory(preferredCategory);
                  const farm = farmOptions.find((item) => String(item.id) === preferredFarm);
                  onSetZipFilter(farm?.zip || "");
                }}
              >
                Apply preferences
              </button>
            </section>

            {isSeller ? (
              <CreateProductForm
                key={editTarget ? `edit-${editTarget.id}` : "create"}
                mode={editTarget ? "edit" : "create"}
                initialData={editTarget}
                onCreate={onCreateProduct}
                onEdit={onSaveEdit}
                loading={editTarget ? savingEdit : savingProduct}
              />
            ) : null}
          </aside>

          <ProductList
            products={products}
            loading={loadingProducts}
            currentUser={currentUser}
            onFocusKeyword={onFocusKeyword}
            onDeleteProduct={onDeleteProduct}
            onPurchase={onPurchase}
            onOpenMessages={onOpenMessages}
            onEditProduct={onEditProduct}
          />
        </div>
      </section>

      <footer className="editorial-footer">
        <div>
          <p className="brand-kicker">The Editorial Harvest</p>
          <strong>Harvest-led commerce for neighbors and growers.</strong>
        </div>
        <div className="editorial-footer__links">
          <button
            className="button button--ghost"
            type="button"
            onClick={() => navigate("/")}
          >
            Home
          </button>
          <button
            className="button button--ghost"
            type="button"
            onClick={() => navigate("/orders")}
          >
            Orders
          </button>
          <button
            className="button button--ghost"
            type="button"
            onClick={() => navigate("/community")}
          >
            Community Trust
          </button>
        </div>
      </footer>
    </div>
  );
}
