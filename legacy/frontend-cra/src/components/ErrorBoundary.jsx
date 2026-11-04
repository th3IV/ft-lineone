import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleReset);
      }

      return (
        <div className="error-boundary" style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "60vh",
          padding: "2rem",
          textAlign: "center",
        }}>
          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: "2rem",
            color: "#1a1a1a",
            marginBottom: "1rem",
          }}>
            Algo salio mal
          </h1>
          <p style={{
            color: "#666",
            marginBottom: "2rem",
            maxWidth: "400px",
          }}>
            Ha ocurrido un error inesperado. Puedes intentar recargar la pagina.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              backgroundColor: "#1a1a1a",
              color: "#fff",
              border: "none",
              padding: "0.75rem 2rem",
              fontSize: "1rem",
              cursor: "pointer",
              fontFamily: "'Inter', sans-serif",
            }}
          >
            Recargar pagina
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
