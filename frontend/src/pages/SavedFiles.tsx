import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getSavedFiles, reprocessFile, deleteFile } from "@/lib/api";
import {
  FileText,
  RefreshCw,
  Calendar,
  User,
  Trash2,
  X,
  AlertTriangle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SavedFile {
  job_id: string;
  file_name: string;
  file_size: number;
  student_name: string;
  student_id: string;
  exam_name: string;
  subject: string;
  uploaded_at: string;
  state: string;
  percentage: number;
}

const SavedFiles: React.FC = () => {
  const [files, setFiles] = useState<SavedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [reprocessing, setReprocessing] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [deleteModal, setDeleteModal] = useState<{
    open: boolean;
    jobId: string;
    examName: string;
  } | null>(null);
  const [toast, setToast] = useState<{
    show: boolean;
    message: string;
    type: "success" | "error";
  } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSavedFiles();
  }, []);

  // Auto-hide toast after 3 seconds
  useEffect(() => {
    if (toast?.show) {
      const timer = setTimeout(() => {
        setToast({ ...toast, show: false });
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const fetchSavedFiles = async () => {
    try {
      setLoading(true);
      const response = await getSavedFiles();
      setFiles(response.data.files);
    } catch (error) {
      console.error("Failed to fetch saved files:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleReprocess = async (jobId: string) => {
    try {
      setReprocessing(jobId);
      const response = await reprocessFile(jobId);
      const newJobId = response.data.new_job_id;

      navigate(`/results/${newJobId}`);
    } catch (error) {
      console.error("Failed to reprocess file:", error);
      setToast({
        show: true,
        message: "Failed to reprocess file",
        type: "error",
      });
    } finally {
      setReprocessing(null);
    }
  };

  const handleDeleteClick = (jobId: string, examName: string) => {
    setDeleteModal({ open: true, jobId, examName });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteModal) return;

    try {
      setDeleting(deleteModal.jobId);
      await deleteFile(deleteModal.jobId);

      // Remove from list
      setFiles(files.filter((file) => file.job_id !== deleteModal.jobId));

      // Show success toast
      setToast({
        show: true,
        message: "File deleted successfully",
        type: "success",
      });
      setDeleteModal(null);
    } catch (error) {
      console.error("Failed to delete file:", error);
      setToast({ show: true, message: "Failed to delete file", type: "error" });
    } finally {
      setDeleting(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case "completed":
        return "bg-green-500/20 text-green-600 border border-green-500/30";
      case "failed":
        return "bg-red-500/20 text-red-600 border border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-600 border border-gray-500/30";
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Toast Notification - Top Right */}
        <AnimatePresence>
          {toast?.show && (
            <motion.div
              initial={{ opacity: 0, x: 100, y: 0 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              exit={{ opacity: 0, x: 100 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="fixed top-20 right-4 z-50"
            >
              <div
                className={`glass-card rounded-lg p-4 shadow-lg border-l-4 ${
                  toast.type === "success"
                    ? "border-green-500"
                    : "border-red-500"
                } flex items-center space-x-3`}
              >
                <div
                  className={`h-2 w-2 rounded-full ${
                    toast.type === "success" ? "bg-green-500" : "bg-red-500"
                  } animate-pulse`}
                ></div>
                <p className="text-sm font-medium">{toast.message}</p>
                <button
                  onClick={() => setToast({ ...toast, show: false })}
                  className="ml-2"
                >
                  <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Delete Confirmation Modal - Centered */}
        <AnimatePresence>
          {deleteModal?.open && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setDeleteModal(null)}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
              />

              {/* Modal */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="fixed inset-0 flex items-center justify-center z-50 p-4"
              >
                <div className="glass-card rounded-2xl p-6 max-w-md w-full shadow-2xl border border-border/50">
                  {/* Icon */}
                  <div className="flex items-center justify-center mb-4">
                    <div className="h-16 w-16 rounded-full bg-red-500/20 flex items-center justify-center">
                      <AlertTriangle className="h-8 w-8 text-red-500" />
                    </div>
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-bold text-center mb-2">
                    Delete Test Paper?
                  </h3>
                  <p className="text-muted-foreground text-center mb-6">
                    Are you sure you want to delete{" "}
                    <span className="font-semibold text-foreground">
                      "{deleteModal.examName}"
                    </span>
                    ? This action cannot be undone.
                  </p>

                  {/* Actions */}
                  <div className="flex space-x-3">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setDeleteModal(null)}
                      className="flex-1 px-4 py-3 rounded-lg border border-border/50 hover:bg-secondary transition-colors font-medium"
                    >
                      Cancel
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleDeleteConfirm}
                      disabled={deleting === deleteModal.jobId}
                      className="flex-1 px-4 py-3 rounded-lg bg-red-500 hover:bg-red-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {deleting === deleteModal.jobId ? (
                        <span className="flex items-center justify-center">
                          <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                          Deleting...
                        </span>
                      ) : (
                        "Delete"
                      )}
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold gradient-text mb-2">
              Saved Files
            </h1>
            <p className="text-muted-foreground">
              View and manage previously uploaded test papers
            </p>
          </div>

          {/* Files Grid */}
          {loading ? (
            <div className="text-center py-12">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="inline-block h-12 w-12 border-4 border-primary border-t-transparent rounded-full"
              />
              <p className="mt-4 text-muted-foreground">Loading files...</p>
            </div>
          ) : files.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-card rounded-2xl p-12 text-center"
            >
              <FileText className="mx-auto h-16 w-16 text-primary mb-4 glow-primary" />
              <h3 className="text-xl font-semibold mb-2">No saved files</h3>
              <p className="text-muted-foreground mb-6">
                Upload a test to get started
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate("/upload")}
                className="px-6 py-3 gradient-primary text-white font-medium rounded-lg shadow-lg"
              >
                Upload Test
              </motion.button>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {files.map((file, index) => (
                <motion.div
                  key={file.job_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass-card rounded-xl p-6 hover:scale-[1.02] transition-all"
                >
                  {/* File Icon and Name */}
                  <div className="flex items-start mb-4">
                    <FileText className="h-10 w-10 text-primary mr-3 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold truncate">
                        {file.exam_name}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.file_size)}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getStateColor(
                        file.state
                      )}`}
                    >
                      {file.state}
                    </span>
                  </div>

                  {/* Student Info */}
                  <div className="space-y-2 mb-4 text-sm">
                    <div className="flex items-center text-muted-foreground">
                      <User className="h-4 w-4 mr-2 text-primary flex-shrink-0" />
                      <span className="truncate">{file.student_name}</span>
                    </div>
                    <div
                      className="text-xs text-muted-foreground truncate"
                      title={file.job_id}
                    >
                      <strong className="text-foreground">ID:</strong>{" "}
                      {file.job_id}
                    </div>
                    <div className="text-muted-foreground">
                      <strong className="text-foreground">Subject:</strong>{" "}
                      {file.subject}
                    </div>
                  </div>

                  {/* Date */}
                  <div className="flex items-center text-xs text-muted-foreground mb-4">
                    <Calendar className="h-4 w-4 mr-1 text-primary" />
                    {(() => {
                      if (!file.uploaded_at) return "Date unavailable";

                      try {
                        const date = new Date(file.uploaded_at);

                        if (isNaN(date.getTime())) return "Invalid date";

                        return date.toLocaleString("en-IN", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                          hour12: true,
                          timeZone: "Asia/Kolkata",
                        });
                      } catch (error) {
                        console.error("Date parsing error:", error);
                        return "Date unavailable";
                      }
                    })()}
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => navigate(`/results/${file.job_id}`)}
                      className="flex-1 px-3 py-2 text-sm font-medium text-primary bg-primary/10 rounded-lg hover:bg-primary/20 transition-colors border border-primary/20"
                    >
                      View Results
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleReprocess(file.job_id)}
                      disabled={reprocessing === file.job_id}
                      className="px-3 py-2 text-sm font-medium text-white gradient-primary rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Reprocess"
                    >
                      {reprocessing === file.job_id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() =>
                        handleDeleteClick(file.job_id, file.exam_name)
                      }
                      className="px-3 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default SavedFiles;
