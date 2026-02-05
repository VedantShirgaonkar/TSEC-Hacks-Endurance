import React, { useState, useRef, useCallback } from 'react';
import { X, Upload, FileText, Check, Loader2, AlertCircle } from 'lucide-react';

const IngestModal = ({ isOpen, onClose }) => {
    const [file, setFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null); // 'success' | 'error' | null
    const [statusMessage, setStatusMessage] = useState('');
    const fileInputRef = useRef(null);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && (droppedFile.name.endsWith('.md') || droppedFile.name.endsWith('.txt'))) {
            setFile(droppedFile);
            setUploadStatus(null);
        } else {
            setUploadStatus('error');
            setStatusMessage('Please upload a .md or .txt file');
        }
    }, []);

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setUploadStatus(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setIsUploading(true);
        setUploadStatus(null);

        try {
            // Read file content
            const content = await file.text();

            // Convert to base64 for safe transmission
            const base64Content = btoa(unescape(encodeURIComponent(content)));

            const response = await fetch('https://onehhynrll.execute-api.ap-south-1.amazonaws.com/prod/ingest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: file.name,
                    content: base64Content,
                    is_base64: true,
                    refresh_embeddings: true,
                }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setUploadStatus('success');
                setStatusMessage(`Document "${file.name}" uploaded successfully!`);
                setTimeout(() => {
                    setFile(null);
                    setUploadStatus(null);
                }, 3000);
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            setUploadStatus('error');
            setStatusMessage(error.message || 'Failed to upload document');
        } finally {
            setIsUploading(false);
        }
    };

    const handleClose = () => {
        if (!isUploading) {
            setFile(null);
            setUploadStatus(null);
            setStatusMessage('');
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={handleClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-md mx-4 bg-bg-secondary border border-border-subtle rounded-2xl shadow-2xl overflow-hidden">

                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-border-subtle">
                    <h2 className="text-lg font-semibold text-text-primary">Upload Document</h2>
                    <button
                        onClick={handleClose}
                        disabled={isUploading}
                        className="p-1 rounded-md text-text-tertiary hover:text-text-primary hover:bg-white/5 transition-colors disabled:opacity-50"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">

                    {/* Drop Zone */}
                    <div
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                        className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 ${isDragging
                                ? 'border-accent-primary bg-accent-primary/10 scale-[1.02]'
                                : file
                                    ? 'border-accent-primary/50 bg-accent-primary/5'
                                    : 'border-border-subtle hover:border-text-tertiary hover:bg-white/5'
                            }`}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".md,.txt"
                            onChange={handleFileSelect}
                            className="hidden"
                        />

                        {file ? (
                            <div className="flex flex-col items-center gap-2 text-center">
                                <div className="w-12 h-12 rounded-lg bg-accent-primary/20 flex items-center justify-center">
                                    <FileText size={24} className="text-accent-primary" />
                                </div>
                                <span className="text-sm font-medium text-text-primary truncate max-w-[200px]">{file.name}</span>
                                <span className="text-xs text-text-tertiary">{(file.size / 1024).toFixed(1)} KB</span>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center gap-3 text-center">
                                <div className="w-14 h-14 rounded-full bg-white/5 flex items-center justify-center">
                                    <Upload size={24} className="text-text-tertiary" />
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-text-primary">Drop your document here</p>
                                    <p className="text-xs text-text-tertiary mt-1">or click to browse (.md, .txt)</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Status Message */}
                    {uploadStatus && (
                        <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-sm ${uploadStatus === 'success'
                                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                                : 'bg-red-500/10 text-red-400 border border-red-500/20'
                            }`}>
                            {uploadStatus === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
                            {statusMessage}
                        </div>
                    )}

                    {/* Upload Button */}
                    <button
                        onClick={handleUpload}
                        disabled={!file || isUploading}
                        className={`w-full mt-4 py-3 px-4 rounded-xl font-medium text-sm transition-all duration-300 flex items-center justify-center gap-2 ${!file || isUploading
                                ? 'bg-white/5 text-text-tertiary cursor-not-allowed'
                                : 'bg-accent-primary text-white hover:bg-accent-primary/90 shadow-lg shadow-accent-primary/20'
                            }`}
                    >
                        {isUploading ? (
                            <>
                                <Loader2 size={18} className="animate-spin" />
                                <span>Uploading & Processing...</span>
                            </>
                        ) : (
                            <>
                                <Upload size={18} />
                                <span>Upload Document</span>
                            </>
                        )}
                    </button>

                    <p className="text-[10px] text-text-tertiary text-center mt-3">
                        Documents will be processed and added to the knowledge base
                    </p>
                </div>
            </div>
        </div>
    );
};

export default IngestModal;
