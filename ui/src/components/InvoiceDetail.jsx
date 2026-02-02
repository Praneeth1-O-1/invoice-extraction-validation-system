import React from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';
import clsx from 'clsx';

const StatusBadge = ({ status }) => {
    const styles = {
        pass: 'bg-green-100 text-green-700 border-green-200',
        warning: 'bg-yellow-50 text-yellow-700 border-yellow-200',
        fail: 'bg-red-100 text-red-700 border-red-200',
    };

    const icons = {
        pass: CheckCircle,
        warning: AlertTriangle,
        fail: XCircle,
    };

    const Icon = icons[status] || Info;

    return (
        <span className={clsx("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border", styles[status])}>
            <Icon className="w-3.5 h-3.5" />
            {status.toUpperCase()}
        </span>
    );
};

const FieldGroup = ({ title, children }) => (
    <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3 border-b border-gray-100 pb-2">{title}</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {children}
        </div>
    </div>
);

const Field = ({ label, value, validation }) => {
    const hasError = validation?.status === 'fail';
    const hasWarning = validation?.status === 'warning';

    return (
        <div className={clsx(
            "p-3 rounded-lg border transition-colors",
            hasError ? "bg-red-50 border-red-200" : hasWarning ? "bg-yellow-50 border-yellow-200" : "bg-white border-gray-200 hover:border-gray-300"
        )}>
            <p className="text-xs text-gray-500 mb-1 flex justify-between">
                {label}
                {hasError && <span className="text-red-600 font-medium text-[10px]">{validation.message}</span>}
            </p>
            <div className="font-medium text-gray-900 break-words">
                {value || <span className="text-gray-400 italic">Not extracted</span>}
            </div>
        </div>
    );
};

const InvoiceDetail = ({ invoice, validationResult }) => {
    if (!invoice) return null;

    const getFieldValidation = (fieldName) => {
        if (!validationResult) return null;

        const error = validationResult.errors?.find(i => i.field === fieldName || i.field?.includes(fieldName));
        if (error) return { status: 'fail', message: error.message };

        const warning = validationResult.warnings?.find(i => i.field === fieldName || i.field?.includes(fieldName));
        if (warning) return { status: 'warning', message: warning.message };

        return null;
    };

    return (
        <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                <div>
                    <h3 className="text-lg font-bold text-gray-900">
                        {invoice.invoice_number || "Unknown Invoice"}
                    </h3>
                    <p className="text-sm text-gray-500">
                        {invoice.seller?.seller_name || "Unknown Vendor"}
                    </p>
                </div>
                <div>
                    {validationResult && (
                        <StatusBadge status={validationResult.is_valid ? 'pass' : 'fail'} />
                    )}
                </div>
            </div>

            <div className="p-6">
                <FieldGroup title="General Information">
                    <Field label="Invoice Number" value={invoice.invoice_number} validation={getFieldValidation('invoice_number')} />
                    <Field label="Invoice Date" value={invoice.invoice_date} validation={getFieldValidation('invoice_date')} />
                    <Field label="Due Date" value={invoice.due_date} validation={getFieldValidation('due_date')} />
                    <Field label="Currency" value={invoice.currency} validation={getFieldValidation('currency')} />
                </FieldGroup>

                <FieldGroup title="Financials">
                    <Field label="Net Total" value={invoice.net_total} validation={getFieldValidation('net_total')} />
                    <Field label="Tax Amount" value={invoice.tax_amount} validation={getFieldValidation('tax_amount')} />
                    <Field label="Tax Rate" value={`${invoice.tax_rate || 0}%`} validation={getFieldValidation('tax_rate')} />
                    <Field label="Gross Total" value={invoice.gross_total} validation={getFieldValidation('gross_total')} />
                </FieldGroup>

                <FieldGroup title="Participants">
                    <Field label="Seller Name" value={invoice.seller?.seller_name} validation={getFieldValidation('seller_name')} />
                    <Field label="Seller Tax ID" value={invoice.seller?.seller_tax_id} validation={getFieldValidation('seller_tax_id')} />
                    <Field label="Buyer Name" value={invoice.buyer?.buyer_name} validation={getFieldValidation('buyer_name')} />
                    <Field label="Buyer Tax ID" value={invoice.buyer?.buyer_tax_id} validation={getFieldValidation('buyer_tax_id')} />
                </FieldGroup>

                {invoice.line_items && invoice.line_items.length > 0 && (
                    <div className="mb-6">
                        <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3 border-b border-gray-100 pb-2">Line Items</h4>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Unit Price</th>
                                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {invoice.line_items.map((item, idx) => (
                                        <tr key={idx}>
                                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{item.description}</td>
                                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-right">{item.quantity}</td>
                                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-right">{item.unit_price}</td>
                                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 text-right font-medium">{item.total_amount}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InvoiceDetail;
