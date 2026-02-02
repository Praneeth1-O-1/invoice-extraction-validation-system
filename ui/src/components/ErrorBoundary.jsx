import React from 'react';
import { AlertTriangle } from 'lucide-react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("ErrorBoundary caught an error", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="p-6 bg-red-50 border border-red-200 rounded-lg flex items-start gap-4">
                    <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
                    <div>
                        <h3 className="text-lg font-semibold text-red-800">Something went wrong</h3>
                        <p className="text-sm text-red-600 mt-1">
                            There was an error loading this component. Please try refreshing the page.
                        </p>
                        <details className="mt-2 text-xs text-red-500 cursor-pointer">
                            <summary>Error Details</summary>
                            <pre className="mt-2 whitespace-pre-wrap">{this.state.error && this.state.error.toString()}</pre>
                        </details>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
