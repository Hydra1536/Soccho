import React from 'react';

type Props = {
  children: React.ReactNode;
};

type State = {
  hasError: boolean;
};

export class AppErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error('Unhandled UI error', error);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F3F4F6] p-6">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-[#E5E7EB] p-6 text-center">
          <h1 className="text-lg font-semibold text-[#111827] mb-2" style={{ fontFamily: 'var(--font-display)' }}>
            Something went wrong
          </h1>
          <p className="text-sm text-[#6B7280] mb-4">Please reload to continue.</p>
          <button onClick={this.handleReload} className="px-4 py-2 rounded-lg bg-[#4F46E5] text-white text-sm hover:bg-[#4338CA] transition-colors">
            Reload
          </button>
        </div>
      </div>
    );
  }
}
