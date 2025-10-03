import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export type Database = {
  public: {
    Tables: {
      users: {
        Row: {
          id: string;
          email: string;
          full_name: string | null;
          avatar_url: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email: string;
          full_name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          full_name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      presets: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          description: string;
          config: any;
          is_public: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          name: string;
          description?: string;
          config: any;
          is_public?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          name?: string;
          description?: string;
          config?: any;
          is_public?: boolean;
          created_at?: string;
          updated_at?: string;
        };
      };
      processing_jobs: {
        Row: {
          id: string;
          user_id: string;
          preset_id: string | null;
          status: 'pending' | 'processing' | 'completed' | 'failed';
          base_video_url: string;
          overlay_video_url: string;
          overlay_audio_url: string;
          config: any;
          progress: number;
          error_message: string | null;
          result_manifest: any | null;
          created_at: string;
          updated_at: string;
          completed_at: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          preset_id?: string | null;
          status?: 'pending' | 'processing' | 'completed' | 'failed';
          base_video_url: string;
          overlay_video_url: string;
          overlay_audio_url: string;
          config: any;
          progress?: number;
          error_message?: string | null;
          result_manifest?: any | null;
          created_at?: string;
          updated_at?: string;
          completed_at?: string | null;
        };
        Update: {
          id?: string;
          user_id?: string;
          preset_id?: string | null;
          status?: 'pending' | 'processing' | 'completed' | 'failed';
          base_video_url?: string;
          overlay_video_url?: string;
          overlay_audio_url?: string;
          config?: any;
          progress?: number;
          error_message?: string | null;
          result_manifest?: any | null;
          created_at?: string;
          updated_at?: string;
          completed_at?: string | null;
        };
      };
      output_clips: {
        Row: {
          id: string;
          job_id: string;
          user_id: string;
          clip_number: number;
          start_time: number;
          end_time: number;
          duration: number;
          ratio: string;
          storage_url: string;
          thumbnail_url: string | null;
          metadata: any;
          created_at: string;
        };
        Insert: {
          id?: string;
          job_id: string;
          user_id: string;
          clip_number: number;
          start_time: number;
          end_time: number;
          duration: number;
          ratio: string;
          storage_url: string;
          thumbnail_url?: string | null;
          metadata?: any;
          created_at?: string;
        };
        Update: {
          id?: string;
          job_id?: string;
          user_id?: string;
          clip_number?: number;
          start_time?: number;
          end_time?: number;
          duration?: number;
          ratio?: string;
          storage_url?: string;
          thumbnail_url?: string | null;
          metadata?: any;
          created_at?: string;
        };
      };
    };
  };
};
