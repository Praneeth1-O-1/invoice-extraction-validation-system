import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { FileText, ShieldCheck } from 'lucide-react';

const Layout = () => {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-900">
            {/* Header */}
            <header className="bg-white border-b border-gray-100 shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16 items-center">
                        {/* Logo / Brand */}
                        <div className="flex items-center">
                            <Link to="/" className="flex items-center gap-2 group">
                                <div className="bg-primary-50 p-2 rounded-lg group-hover:bg-primary-100 transition-colors">
                                    <ShieldCheck className="h-6 w-6 text-primary-600" />
                                </div>
                                <div>
                                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
                                        InvoiceQC
                                    </h1>
                                </div>
                            </Link>
                        </div>

                        {/* Navigation (Simple) */}
                        <nav className="flex space-x-6">
                            <Link to="/" className="text-sm font-medium text-gray-500 hover:text-primary-600 transition-colors">
                                Upload
                            </Link>
                            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
                                API Docs
                            </a>
                        </nav>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-grow py-8 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <Outlet />
                </div>
            </main>

            {/* Footer */}
            <footer className="bg-white border-t border-gray-100 py-6 mt-auto">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-center text-sm text-gray-400">
                    <p>© 2024 InvoiceQC System. Internal Use Only.</p>
                </div>
            </footer>
        </div>
    );
};

export default Layout;
