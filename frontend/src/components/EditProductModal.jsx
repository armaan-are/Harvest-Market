import CreateProductForm from "./CreateProductForm";

export default function EditProductModal({
  product,
  loading = false,
  onClose,
  onSave,
}) {
  if (!product) {
    return null;
  }

  return (
    <div className="modal-overlay" role="presentation" onMouseDown={onClose}>
      <section
        className="edit-product-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-product-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="messages-modal__header">
          <div>
            <p className="eyebrow">Seller Studio</p>
            <h2 id="edit-product-title">Edit {product.title}</h2>
          </div>
          <button className="button button--ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <CreateProductForm
          mode="edit"
          initialData={product}
          onEdit={onSave}
          onCancel={onClose}
          loading={loading}
        />
      </section>
    </div>
  );
}
