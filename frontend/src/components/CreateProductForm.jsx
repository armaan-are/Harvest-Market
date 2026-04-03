import { useEffect, useState } from "react";

export default function CreateProductForm({
  mode = "create",            // "create" | "edit"
  initialData = null,         // { title, description, price, image_url }
  onCreate,
  onEdit,
  loading = false,
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [imageUrl, setImageUrl] = useState("");

  // When editing, fill the form with initialData
  useEffect(() => {
    if (mode === "edit" && initialData) {
      setTitle(initialData.title);
      setDescription(initialData.description);
      setPrice(initialData.price);
      setImageUrl(initialData.image_url || "");
    }
  }, [mode, initialData]);

  function handleSubmit(e) {
    e.preventDefault();

    const formData = {
      title,
      description,
      price: parseFloat(price),
      image_url: imageUrl,
    };

    if (mode === "edit") {
      onEdit(formData);
    } else {
      onCreate(formData);
    }
  }

  return (
    <div
      style={{
        padding: "16px",
        borderRadius: "10px",
        border: "1px solid #e5e7eb",
        marginBottom: "24px",
        backgroundColor: "rgba(255, 255, 255, 0.95)",
      }}
    >
      <h2 style={{ marginBottom: "8px" }}>
        {mode === "edit" ? "Edit Product" : "Create Product (Seller Only)"}
      </h2>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "8px" }}>
          <label>
            Title:
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              style={{
                marginLeft: "8px",
                padding: "6px",
                borderRadius: "4px",
                border: "1px solid #d1d5db",
                minWidth: "260px",
              }}
            />
          </label>
        </div>

        <div style={{ marginBottom: "8px" }}>
          <label>
            Description:
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{
                marginLeft: "8px",
                padding: "6px",
                borderRadius: "4px",
                border: "1px solid #d1d5db",
                minWidth: "260px",
              }}
            />
          </label>
        </div>

        <div style={{ marginBottom: "8px" }}>
          <label>
            Price:
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              required
              style={{
                marginLeft: "8px",
                padding: "6px",
                borderRadius: "4px",
                border: "1px solid #d1d5db",
                minWidth: "120px",
              }}
            />
          </label>
        </div>

        <div style={{ marginBottom: "8px" }}>
          <label>
            Image URL:
            <input
              type="text"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="/fruits/apple1.png"
              style={{
                marginLeft: "8px",
                padding: "6px",
                borderRadius: "4px",
                border: "1px solid #d1d5db",
                minWidth: "260px",
              }}
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "8px 16px",
            borderRadius: "6px",
            border: "none",
            backgroundColor: mode === "edit" ? "#3b82f6" : "#10b981",
            color: "#ffffff",
            cursor: "pointer",
          }}
        >
          {loading ? "Saving..." : mode === "edit" ? "Save Changes" : "Create Product"}
        </button>
      </form>
    </div>
  );
}