import React, { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import InvoiceDetail from '../components/InvoiceDetail';
import ErrorBoundary from '../components/ErrorBoundary';
import { ChevronLeft, FileText, CheckCircle, XCircle } from 'lucide-react';
import clsx from 'clsx';

const ResultsPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [selectedInvoiceIndex, setSelectedInvoiceIndex] = useState(0);

    // Data from previous page
    const data = location.state?.data;

    useEffect(() => {
        if (!data) {
            navigate('/');
        }
    }, [data, navigate]);

    if (!data) return null;

    const { extracted_invoices, validation_report } = data;
    const validationResults = validation_report?.results || [];

    return (
        <div className="flex h-[calc(100vh-8rem)]">
            {/* Sidebar - Invoice List */}
            <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto hidden md:block">
                <div className="p-4 border-b border-gray-100">
                    <Link to="/" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1 font-medium mb-4">
                        <ChevronLeft className="w-4 h-4" />
                        Upload New
                    </Link>
                    <h2 className="text-lg font-bold text-gray-900">Invoices ({extracted_invoices.length})</h2>
                </div>
                <ul className="divide-y divide-gray-100">
                    {extracted_invoices.map((invoice, idx) => {
                        const isValid = validationResults[idx]?.is_valid;
                        return (
                            <li key={idx}>
                                <button
                                    onClick={() => setSelectedInvoiceIndex(idx)}
                                    className={clsx(
                                        "w-full text-left p-4 hover:bg-gray-50 transition-colors border-l-4",
                                        selectedInvoiceIndex === idx
                                            ? "bg-primary-50 border-primary-500"
                                            : "border-transparent"
                                    )}
                                >
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-sm font-medium text-gray-900 truncate">
                                            {invoice.invoice_number || "No Number"}
                                        </span>
                                        {isValid ? (
                                            <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                                        ) : (
                                            <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500 truncate">
                                        {invoice.seller?.seller_name || "Unknown Vendor"}
                                    </p>
                                    <p className="text-xs text-gray-400 mt-1">
                                        {invoice.invoice_date}
                                    </p>
                                </button>
                            </li>
                        );
                    })}
                </ul>
            </div>

            {/* Main Content - Detail View */}
            <div className="flex-1 overflow-y-auto bg-gray-50 p-6 md:p-8">
                <div className="max-w-4xl mx-auto">
                    {extracted_invoices.length > 0 ? (
                        <ErrorBoundary>
                            <InvoiceDetail
                                invoice={extracted_invoices[selectedInvoiceIndex]}
                                validationResult={validationResults[selectedInvoiceIndex]}
                            />
                        </ErrorBoundary>
                    ) : (
                        <div className="text-center py-12">
                            <p className="text-gray-500">No invoices extracted.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ResultsPage;
