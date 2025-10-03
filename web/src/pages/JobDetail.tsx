import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function JobDetail() {
  const { id } = useParams();
  const [job, setJob] = useState<any>(null);
  const [clips, setClips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobDetails();
  }, [id]);

  const fetchJobDetails = async () => {
    if (!id) return;

    const { data: jobData } = await supabase
      .from('processing_jobs')
      .select('*')
      .eq('id', id)
      .single();

    const { data: clipsData } = await supabase
      .from('output_clips')
      .select('*')
      .eq('job_id', id)
      .order('clip_number');

    if (jobData) setJob(jobData);
    if (clipsData) setClips(clipsData);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Job not found</p>
        <Link to="/" className="btn-primary inline-flex mt-4">Back to Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Job Details</h1>
        <Link to="/" className="btn-secondary">Back to Dashboard</Link>
      </div>

      <div className="card">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className="text-lg font-semibold capitalize">{job.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Progress</p>
            <p className="text-lg font-semibold">{job.progress}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Clips Generated</p>
            <p className="text-lg font-semibold">{clips.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Created</p>
            <p className="text-lg font-semibold">{new Date(job.created_at).toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      {clips.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Output Clips</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {clips.map((clip) => (
              <div key={clip.id} className="border border-gray-200 rounded-lg p-4">
                <div className="aspect-video bg-gray-100 rounded mb-2"></div>
                <p className="text-sm font-medium">Clip #{clip.clip_number}</p>
                <p className="text-xs text-gray-500">{clip.duration}s • {clip.ratio}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
