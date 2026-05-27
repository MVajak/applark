import { type FormEvent, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { Button, Input, Label, Tabs, TabsContent, TabsList, TabsTrigger, Textarea } from '@applark/ui';

import { getErrorDetail, getErrorDetailObject, getErrorStatus } from '@/domains/api/client';
import { getGetJobsQueryKey, useCreateJobFromText, useCreateJobFromUrl } from '@/domains/api/generated/jobs/jobs';

function handleDuplicate(err: unknown, navigate: ReturnType<typeof useNavigate>, onCreated: () => void): boolean {
  if (getErrorStatus(err) !== 409) return false;
  const detail = getErrorDetailObject(err);
  const existingId = detail?.existing_job_id;
  if (typeof existingId !== 'string') return false;
  toast('This URL is already on your list — opening it.');
  onCreated();
  navigate(`/jobs/${existingId}`);
  return true;
}

export function JobCreateForm({ onCreated }: { onCreated: () => void }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const invalidateJobs = () => queryClient.invalidateQueries({ queryKey: getGetJobsQueryKey() });

  const fromUrl = useCreateJobFromUrl({
    mutation: {
      onSuccess: async () => {
        await invalidateJobs();
        toast.success('Job queued — scraping…');
        onCreated();
      },
      onError: (err) => {
        if (handleDuplicate(err, navigate, onCreated)) return;
        toast.error(getErrorDetail(err) ?? 'Failed to add job from URL');
      },
    },
  });

  const fromText = useCreateJobFromText({
    mutation: {
      onSuccess: async () => {
        await invalidateJobs();
        toast.success('Job queued — extracting…');
        onCreated();
      },
      onError: (err) => {
        if (handleDuplicate(err, navigate, onCreated)) return;
        toast.error(getErrorDetail(err) ?? 'Failed to add job from text');
      },
    },
  });

  const [url, setUrl] = useState('');
  const [rawText, setRawText] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');

  const submitUrl = (event: FormEvent) => {
    event.preventDefault();
    if (!url.trim()) {
      toast.error('Paste a URL first');
      return;
    }
    fromUrl.mutate({ data: { source_url: url.trim() } });
  };

  const submitText = (event: FormEvent) => {
    event.preventDefault();
    if (!rawText.trim()) {
      toast.error('Paste the posting text first');
      return;
    }
    fromText.mutate({
      data: {
        raw_text: rawText,
        source_url: sourceUrl.trim() ? sourceUrl.trim() : null,
      },
    });
  };

  return (
    <Tabs defaultValue="url" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="url">From URL</TabsTrigger>
        <TabsTrigger value="text">From Text</TabsTrigger>
      </TabsList>

      <TabsContent value="url" className="mt-4">
        <form onSubmit={submitUrl} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="job-url">Job posting URL</Label>
            <Input
              id="job-url"
              type="url"
              placeholder="https://example.com/jobs/12345"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={fromUrl.isPending}>
              {fromUrl.isPending ? 'Adding…' : 'Add'}
            </Button>
          </div>
        </form>
      </TabsContent>

      <TabsContent value="text" className="mt-4">
        <form onSubmit={submitText} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="job-text">Job posting text</Label>
            <Textarea
              id="job-text"
              rows={10}
              placeholder="Paste the full job posting here…"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="job-source-url">Source URL (optional)</Label>
            <Input
              id="job-source-url"
              type="url"
              placeholder="https://example.com/jobs/12345"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={fromText.isPending}>
              {fromText.isPending ? 'Adding…' : 'Add'}
            </Button>
          </div>
        </form>
      </TabsContent>
    </Tabs>
  );
}
