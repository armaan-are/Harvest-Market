import { useEffect, useState } from "react";

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

  useEffect(() => {
    setNewMessage("");
  }, [product?.id]);

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!product) return null;

  async function handleSubmit(event) {
    event.preventDefault();
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
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <section
        className="messages-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="messages-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="messages-modal__header">
          <div>
            <p className="eyebrow">Product Conversation</p>
            <h2 id="messages-title">{product.title}</h2>
          </div>
          <button className="button button--ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        {messagesLoading ? (
          <div className="empty-state empty-state--compact">
            <h3>Loading messages...</h3>
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-state empty-state--compact">
            <h3>No messages yet.</h3>
            <p>Start the conversation with a quick question about this listing.</p>
          </div>
        ) : (
          <div className="message-thread">
            {messages.map((message) => (
              <article
                key={message.id}
                className={
                  message.sender_id === currentUser?.id
                    ? "message-bubble message-bubble--mine"
                    : "message-bubble"
                }
              >
                <header>
                  <strong>{message.sender_email || message.sender_role}</strong>
                  <span>{new Date(message.created_at).toLocaleString()}</span>
                </header>
                <p>{message.content}</p>
              </article>
            ))}
          </div>
        )}

        {messageError ? <div className="error-banner">{messageError}</div> : null}

        {currentUser ? (
          <form className="message-form" onSubmit={handleSubmit}>
            <input
              type="text"
              value={newMessage}
              onChange={(event) => setNewMessage(event.target.value)}
              placeholder="Type your message..."
              maxLength={500}
            />
            <button className="button button--primary" type="submit" disabled={sending}>
              {sending ? "Sending..." : "Send"}
            </button>
          </form>
        ) : (
          <p className="muted-copy">Please sign in to send messages.</p>
        )}
      </section>
    </div>
  );
}
