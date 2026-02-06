import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory } from "@/lib/api";
import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';

interface HistoryItem {
  job_id: string;
  student_name: string;
  student_id: string;
  exam_name: string;
  subject: string;
  percentage: number;
  grade: string;
  state: string;
  created_at: string;
  total_marks: number;
  total_marks_obtained: number;
}

const History: React.FC = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory();
  }, [filter]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? { status: filter } : {};
      const response = await getHistory(params);
      setHistory(response.data.history);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'completed':
        return 'bg-green-500/20 text-green-600 border border-green-500/30';
      case 'failed':
        return 'bg-red-500/20 text-red-600 border border-red-500/30';
      case 'processing':
      case 'assessing':
      case 'generating_feedback':
        return 'bg-yellow-500/20 text-yellow-600 border border-yellow-500/30';
      default:
        return 'bg-gray-500/20 text-gray-600 border border-gray-500/30';
    }
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A':
        return 'text-green-600 font-bold';
      case 'B':
        return 'text-blue-600 font-bold';
      case 'C':
        return 'text-yellow-600 font-bold';
      case 'D':
      case 'F':
        return 'text-red-600 font-bold';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="container mx-auto px-4 max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold gradient-text mb-2">
              Test History
            </h1>
            <p className="text-muted-foreground">
              View and manage your past test submissions
            </p>
          </div>

          {/* Filter Tabs */}
          <div className="mb-6 border-b border-border/50">
            <nav className="-mb-px flex space-x-8">
              {['all', 'completed', 'failed', 'processing'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setFilter(tab)}
                  className={`${
                    filter === tab
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize transition-colors`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          {/* History Grid */}
          {loading ? (
            <div className="text-center py-12">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="inline-block h-12 w-12 border-4 border-primary border-t-transparent rounded-full"
              />
              <p className="mt-4 text-muted-foreground">Loading history...</p>
            </div>
          ) : history.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-card rounded-2xl p-12 text-center"
            >
              <FileText className="mx-auto h-16 w-16 text-primary mb-4 glow-primary" />
              <h3 className="text-xl font-semibold mb-2">No history found</h3>
              <p className="text-muted-foreground mb-6">
                Upload a test to get started
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/upload')}
                className="px-6 py-3 gradient-primary text-white font-medium rounded-lg shadow-lg"
              >
                Upload Test
              </motion.button>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {history.map((item, index) => (
                <motion.div
                  key={item.job_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass-card rounded-xl p-6 cursor-pointer hover:scale-[1.02] transition-all"
                  onClick={() => navigate(`/results/${item.job_id}`)}
                >
                  {/* Status Badge */}
                  <div className="flex justify-between items-start mb-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${getStateColor(
                        item.state
                      )}`}
                    >
                      {item.state}
                    </span>
                    {item.grade !== 'N/A' && (
                      <span className={`text-2xl ${getGradeColor(item.grade)}`}>
                        {item.grade}
                      </span>
                    )}
                  </div>

                  {/* Student Info */}
                  <h3 className="text-lg font-semibold mb-1">
                    {item.student_name}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    ID: {item.student_id}
                  </p>

                  {/* Exam Details */}
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Exam:</span>
                      <span className="font-medium">
                        {item.exam_name}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Subject:</span>
                      <span className="font-medium">
                        {item.subject}
                      </span>
                    </div>
                  </div>

                  {/* Score */}
                  {item.state === 'completed' && (
                    <div className="border-t border-border/50 pt-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Score:</span>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-primary">
                            {item.percentage.toFixed(1)}%
                          </span>
                          <p className="text-xs text-muted-foreground">
                            {item.total_marks_obtained.toFixed(1)}/{item.total_marks}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Date */}
                  <div className="mt-4 text-xs text-muted-foreground">
                    {(() => {
                      if (!item.created_at) return 'Date unavailable';
                      
                      try {
                        const date = new Date(item.created_at);
                        
                        if (isNaN(date.getTime())) return 'Invalid date';
                        
                        return date.toLocaleString('en-IN', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          hour12: true,
                          timeZone: 'Asia/Kolkata',
                        });
                      } catch (error) {
                        console.error('Date parsing error:', error, 'Value:', item.created_at);
                        return 'Date error';
                      }
                    })()}
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

export default History;
