import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { File, Play, Trash2, ArrowLeft } from 'lucide-react';
import { reprocessFile } from '@/lib/api';

const FileDetail: React.FC = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(false);

  const handleProcess = async () => {
    if (!jobId) return;
    
    try {
      setProcessing(true);
      const response = await reprocessFile(jobId);
      navigate(`/results/${response.data.new_job_id}`);
    } catch (error) {
      console.error('Reprocess failed:', error);
      alert('Failed to process file');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background/95 to-primary/5 py-20 px-4">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate('/upload')}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Files
        </button>

        <div className="glass-card p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-4 rounded-lg bg-primary/10">
              <File className="h-10 w-10 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold gradient-text">File Details</h2>
              <p className="text-muted-foreground">Ready to process</p>
            </div>
          </div>

          <div className="flex gap-4">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleProcess}
              disabled={processing}
              className="flex-1 py-4 bg-primary text-primary-foreground rounded-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Play className="h-5 w-5" />
              {processing ? 'Processing...' : 'Process File'}
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-6 py-4 bg-destructive/10 text-destructive rounded-lg font-semibold"
            >
              <Trash2 className="h-5 w-5" />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileDetail;
