import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

export default function Presets() {
  const { user } = useAuth();
  const [presets, setPresets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPresets();
  }, []);

  const fetchPresets = async () => {
    if (!user) return;

    const { data } = await supabase
      .from('presets')
      .select('*')
      .or(`user_id.eq.${user.id},is_public.eq.true`)
      .order('created_at', { ascending: false });

    if (data) setPresets(data);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Presets</h1>
        <button className="btn-primary">Create Preset</button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : presets.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No presets yet</p>
          <button className="btn-primary">Create Your First Preset</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {presets.map((preset) => (
            <div key={preset.id} className="card hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{preset.name}</h3>
                {preset.is_public && (
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">Public</span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-4">{preset.description || 'No description'}</p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{new Date(preset.created_at).toLocaleDateString()}</span>
                <button className="text-primary-600 hover:text-primary-700 font-medium">Use Preset</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
