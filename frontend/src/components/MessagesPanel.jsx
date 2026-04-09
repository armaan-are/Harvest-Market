import { useState } from "react";

/**
 * Message panel for a specific product (buyer & seller chat).
 */
export default function MessagesPanel({
  product,
  messages,
  messagesLoading,
  messageError,
  currentUser,
  onClose,
  onSendMessage,
}) {
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);

  if (!product) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = newMessage.trim();
    if (!trimmed) return;

    setSending(true);
    try {
      await onSendMessage(trimmed);
      setNewMessage("");
    } finally {
      setSending(false);
    }
  }

  return (
    <div
      style={{
        marginTop: "16px",
        marginBottom: "24px",
        padding: "16px",
        borderRadius: "10px",
        border: "1px solid #e5e7eb",
        backgroundColor: "rgba(255, 255, 255, 0.95)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "8px",
        }}
      >
        <h2 style={{ margin: 0 }}>Messages about: {product.title}</h2>
        <button
          type="button"
          onClick={onClose}
          style={{
            padding: "4px 8px",
            borderRadius: "6px",
            border: "1px solid #d1d5db",
            backgroundColor: "#ffffff",
            cursor: "pointer",
          }}
        >
          Close
        </button>
      </div>

      {messagesLoading ? (
        <p>Loading messages...</p>
      ) : messages.length === 0 ? (
        <p>No messages yet. Be the first to ask a question!</p>
      ) : (
        <div
          style={{
            maxHeight: "240px",
            overflowY: "auto",
            marginBottom: "8px",
            paddingRight: "4px",
          }}
        >
          {messages.map((m) => (
            <div
              key={m.id}
              style={{
                marginBottom: "6px",
                padding: "6px 8px",
                borderRadius: "6px",
                backgroundColor:
                  m.sender_id === currentUser?.id ? "#dbeafe" : "#f3f4f6",
              }}
            >
              <div
                style={{
                  fontSize: "12px",
                  color: "#6b7280",
                  marginBottom: "2px",
                }}
              >
                {m.sender_email || m.sender_role} •{" "}
                {new Date(m.created_at).toLocaleString()}
              </div>
              <div>{m.content}</div>
            </div>
          ))}
        </div>
      )}

      {messageError && (
        <div style={{ color: "red", marginBottom: "8px" }}>
          {messageError}
        </div>
      )}

      {currentUser ? (
        <form onSubmit={handleSubmit}>
          <div style={{ display: "flex", gap: "8px" }}>
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type your message..."
              style={{
                flex: 1,
                padding: "8px",
                borderRadius: "6px",
                border: "1px solid #d1d5db",
              }}
            />
            <button
              type="submit"
              disabled={sending}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: "#2563eb",
                color: "#ffffff",
                cursor: "pointer",
              }}
            >
              {sending ? "Sending..." : "Send"}
            </button>
          </div>
        </form>
      ) : (
        <p style={{ fontSize: "14px" }}>Please log in to send messages.</p>
      )}
    </div>
  );
}