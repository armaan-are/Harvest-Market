import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <main className="runtime-error">
          <div className="runtime-error__card">
            <p className="eyebrow">Frontend Runtime Error</p>
            <h1>The app hit a render error.</h1>
            <pre>{String(this.state.error?.message || this.state.error)}</pre>
          </div>
        </main>
      );
    }

    return this.props.children;
  }
}
