import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

export class VkErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error.message || "Непредвиденная ошибка",
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[VK Mini App]", error, info.componentStack);
  }

  private handleReset = () => {
    this.setState({ hasError: false, message: "" });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="vk-mini-app vk-error-boundary">
          <div className="vk-error-boundary-inner">
            <p className="vk-mini-eyebrow">Пушкинские Горы</p>
            <h1 className="vk-mini-title">Что-то пошло не так</h1>
            <p className="text-sm text-muted-foreground">
              Мини-приложение столкнулось с ошибкой. Попробуйте перезагрузить страницу.
            </p>
            <button type="button" className="literary-btn literary-btn--primary mt-3" onClick={this.handleReset}>
              Перезагрузить
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
