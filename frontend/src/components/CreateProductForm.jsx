import { useEffect, useMemo, useState } from "react";

export default function CreateProductForm({
  mode = "create",
  initialData = null,
  onCreate,
  onEdit,
  onCancel,
  loading = false,
}) {
  const defaults = getDefaults(mode, initialData);
  const [title, setTitle] = useState(defaults.title);
  const [description, setDescription] = useState(defaults.description);
  const [price, setPrice] = useState(defaults.price);
  const [quantityAvailable, setQuantityAvailable] = useState(defaults.quantityAvailable);
  const [imageUrl, setImageUrl] = useState(defaults.imageUrl);
  const [category, setCategory] = useState(defaults.category);
  const [imageFile, setImageFile] = useState(null);
  const imagePreview = useMemo(
    () => (imageFile ? URL.createObjectURL(imageFile) : imageUrl),
    [imageFile, imageUrl]
  );

  useEffect(() => {
    if (!imagePreview || !imageFile) return undefined;
    return () => URL.revokeObjectURL(imagePreview);
  }, [imageFile, imagePreview]);

  function handleSubmit(event) {
    event.preventDefault();

    const formData = {
      title,
      description,
      price: Number.parseFloat(price),
      quantity_available: Number.parseInt(quantityAvailable, 10),
      image_url: imageUrl,
      category,
      imageFile,
    };

    if (mode === "edit") {
      onEdit?.(formData);
    } else {
      onCreate(formData);
      setTitle("");
      setDescription("");
      setPrice("");
      setQuantityAvailable("1");
      setImageUrl("");
      setCategory("produce");
      setImageFile(null);
    }
  }

  return (
    <section className="seller-panel">
      <div className="section-heading section-heading--inline">
        <div>
          <p className="eyebrow">Seller Studio</p>
          <h2>{mode === "edit" ? "Update your listing" : "Publish a fresh listing"}</h2>
        </div>
      </div>

      <form className="seller-form" onSubmit={handleSubmit}>
        <label>
          Product title
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
            placeholder="Heirloom tomatoes"
          />
        </label>

        <label>
          Description
          <textarea
            rows="3"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Share what makes this item special."
          />
        </label>

        <div className="seller-form__row">
          <label>
            Price
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(event) => setPrice(event.target.value)}
              required
              placeholder="7.50"
            />
          </label>

          <label>
            Quantity
            <input
              type="number"
              min="0"
              step="1"
              value={quantityAvailable}
              onChange={(event) => setQuantityAvailable(event.target.value)}
              required
              placeholder="10"
            />
          </label>
        </div>

        <label>
          Category
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="produce">Produce</option>
            <option value="dairy">Dairy</option>
            <option value="meat">Meat</option>
            <option value="baked_goods">Baked Goods</option>
          </select>
        </label>

        <label>
          Upload image file
          <input
            type="file"
            accept="image/*"
            onChange={(event) => setImageFile(event.target.files?.[0] || null)}
          />
        </label>

        {imagePreview ? (
          <div className="image-preview">
            <img
              src={imagePreview}
              alt="Listing preview"
              onError={(event) => {
                event.currentTarget.style.display = "none";
              }}
            />
            <span>{imageFile ? imageFile.name : "Current listing image"}</span>
          </div>
        ) : null}

        <details className="advanced-field">
          <summary>Use an existing image path instead</summary>
          <label>
            Image path
            <input
              type="text"
              value={imageUrl}
              onChange={(event) => setImageUrl(event.target.value)}
              placeholder="/fruits/apple1.png"
            />
          </label>
        </details>

        <div className="seller-form__actions">
          {mode === "edit" && onCancel ? (
            <button className="button button--ghost" type="button" onClick={onCancel}>
              Cancel
            </button>
          ) : null}
          <button className="button button--primary" type="submit" disabled={loading}>
            {loading ? "Saving..." : mode === "edit" ? "Save Changes" : "Create Product"}
          </button>
        </div>
      </form>
    </section>
  );
}

function getDefaults(mode, initialData) {
  if (mode === "edit" && initialData) {
    return {
      title: initialData.title,
      description: initialData.description,
      price: String(initialData.price),
      quantityAvailable: String(initialData.quantity_available ?? 1),
      imageUrl: initialData.image_url || "",
      category: initialData.category || "produce",
    };
  }

  return {
    title: "",
    description: "",
    price: "",
    quantityAvailable: "1",
    imageUrl: "",
    category: "produce",
  };
}
