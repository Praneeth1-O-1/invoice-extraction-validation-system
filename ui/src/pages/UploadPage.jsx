import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUploader from '../components/FileUploader';
import { invoiceService } from '../services/api';
import { AlertCircle } from 'lucide-react';

const UploadPage = () => {
    const [files, setFiles] = useState([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleUpload = async () => {
        if (files.length === 0) return;

        setIsProcessing(true);
        setError(null);

        try {
            const result = await invoiceService.extractAndValidate(files);
            // Navigate to results page with the data
            navigate('/results', { state: { data: result } });
        } catch (err) {
            console.error(err);
            setError('Failed to process files. Please try again or check if the backend is running.');
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="text-center space-y-4 pt-8">
                <h2 className="text-4xl font-extrabold tracking-tight text-gray-900">
                    Smart Invoice Processing
                </h2>
                <p className="text-lg text-gray-500 max-w-2xl mx-auto">
                    Upload your PDF invoices to automatically extract data and validate against business rules.
                </p>
            </div>

            {error && (
                <div className="max-w-2xl mx-auto bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                    <p className="text-red-700 text-sm">{error}</p>
                </div>
            )}

            <FileUploader
                files={files}
                onFilesChange={setFiles}
                onUpload={handleUpload}
                isProcessing={isProcessing}
            />

            <div className="max-w-4xl mx-auto mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
                    <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        1
                    </div>
                    <h3 className="font-semibold text-gray-900">Upload PDF</h3>
                    <p className="text-sm text-gray-500 mt-2">Drag and drop your invoices directly into the secure upload area.</p>
                </div>
                <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
                    <div className="w-10 h-10 bg-purple-50 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        2
                    </div>
                    <h3 className="font-semibold text-gray-900">AI Extraction</h3>
                    <p className="text-sm text-gray-500 mt-2">Our system automatically parses key details like vendors, dates, and amounts.</p>
                </div>
                <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
                    <div className="w-10 h-10 bg-green-50 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        3
                    </div>
                    <h3 className="font-semibold text-gray-900">Instant Validation</h3>
                    <p className="text-sm text-gray-500 mt-2">Get immediate feedback on data quality and business rule compliance.</p>
                </div>
            </div>
        </div>
    );
};

export default UploadPage;
