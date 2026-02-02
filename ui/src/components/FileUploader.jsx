import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';
import clsx from 'clsx';

const FileUploader = ({ files, onFilesChange, onUpload, isProcessing }) => {
    const onDrop = useCallback((acceptedFiles) => {
        // Check if files are PDFs
        const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
        if (pdfFiles.length !== acceptedFiles.length) {
            alert('Only PDF files are allowed');
        }

        onFilesChange((prev) => [...prev, ...pdfFiles]);
    }, [onFilesChange]);

    const removeFile = (index) => {
        onFilesChange((prev) => prev.filter((_, i) => i !== index));
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
        },
        disabled: isProcessing,
    });

    return (
        <div className="w-full max-w-2xl mx-auto space-y-6">
            <div
                {...getRootProps()}
                className={clsx(
                    "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ease-in-out",
                    isDragActive ? "border-primary-500 bg-primary-50" : "border-gray-200 hover:border-primary-400 hover:bg-gray-50",
                    isProcessing && "opacity-50 cursor-not-allowed"
                )}
            >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center gap-4">
                    <div className="p-4 bg-primary-100 rounded-full text-primary-600">
                        <UploadCloud className="w-8 h-8" />
                    </div>
                    <div>
                        <p className="text-lg font-medium text-gray-900">
                            {isDragActive ? "Drop invoices here" : "Click to upload or drag and drop"}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                            Supports PDF invoices
                        </p>
                    </div>
                </div>
            </div>

            {files.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                        <h3 className="font-medium text-gray-700">Selected Files ({files.length})</h3>
                        <button
                            onClick={() => onFilesChange([])}
                            className="text-xs text-red-500 hover:text-red-700 font-medium"
                            disabled={isProcessing}
                        >
                            Clear All
                        </button>
                    </div>
                    <ul className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
                        {files.map((file, index) => (
                            <li key={`${file.name}-${index}`} className="px-4 py-3 flex items-center justify-between hover:bg-gray-50">
                                <div className="flex items-center gap-3">
                                    <FileIcon className="w-5 h-5 text-gray-400" />
                                    <div>
                                        <p className="text-sm font-medium text-gray-900 truncate max-w-xs">{file.name}</p>
                                        <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                                    </div>
                                </div>
                                {!isProcessing && (
                                    <button
                                        onClick={() => removeFile(index)}
                                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                )}
                            </li>
                        ))}
                    </ul>
                    <div className="p-4 bg-gray-50 border-t border-gray-100 flex justify-end">
                        <button
                            onClick={onUpload}
                            disabled={isProcessing || files.length === 0}
                            className={clsx(
                                "px-6 py-2.5 rounded-lg font-medium text-white shadow-sm transition-all focus:ring-2 focus:ring-offset-2 focus:ring-primary-500",
                                isProcessing || files.length === 0
                                    ? "bg-gray-300 cursor-not-allowed"
                                    : "bg-primary-600 hover:bg-primary-700 hover:shadow-md active:transform active:scale-95"
                            )}
                        >
                            {isProcessing ? (
                                <span className="flex items-center gap-2">
                                    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Processing...
                                </span>
                            ) : (
                                "Extract & Validate"
                            )}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FileUploader;
