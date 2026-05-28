import { type FormEvent, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { i18n, useTranslation } from '@applark/i18n';
import { Button, Input, Label, Tabs, TabsContent, TabsList, TabsTrigger, Textarea } from '@applark/ui';

import { getErrorDetail, getErrorDetailObject, getErrorStatus } from '@/domains/api/client';
import { getGetJobsQueryKey, useCreateJobFromText, useCreateJobFromUrl } from '@/domains/api/generated/jobs/jobs';

function handleDuplicate(err: unknown, navigate: ReturnType<typeof useNavigate>, onCreated: () => void): boolean {
  if (getErrorStatus(err) !== 409) return false;
  const detail = getErrorDetailObject(err);
  const existingId = detail?.existing_job_id;
  if (typeof existingId !== 'string') return false;
  toast(i18n.t('jobs.create.toastDuplicate'));
  onCreated();
  navigate(`/jobs/${existingId}`);
  return true;
}

export function JobCreateForm({ onCreated }: { onCreated: () => void }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const invalidateJobs = () => queryClient.invalidateQueries({ queryKey: getGetJobsQueryKey() });

  const fromUrl = useCreateJobFromUrl({
    mutation: {
      onSuccess: async () => {
        await invalidateJobs();
        toast.success(t('jobs.create.toastScraping'));
        onCreated();
      },
      onError: (err) => {
        if (handleDuplicate(err, navigate, onCreated)) return;
        toast.error(getErrorDetail(err) ?? t('jobs.create.errorFromUrl'));
      },
    },
  });

  const fromText = useCreateJobFromText({
    mutation: {
      onSuccess: async () => {
        await invalidateJobs();
        toast.success(t('jobs.create.toastExtracting'));
        onCreated();
      },
      onError: (err) => {
        if (handleDuplicate(err, navigate, onCreated)) return;
        toast.error(getErrorDetail(err) ?? t('jobs.create.errorFromText'));
      },
    },
  });

  const [url, setUrl] = useState('');
  const [rawText, setRawText] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');

  const submitUrl = (event: FormEvent) => {
    event.preventDefault();
    if (!url.trim()) {
      toast.error(t('jobs.create.errorPasteUrl'));
      return;
    }
    fromUrl.mutate({ data: { source_url: url.trim() } });
  };

  const submitText = (event: FormEvent) => {
    event.preventDefault();
    if (!rawText.trim()) {
      toast.error(t('jobs.create.errorPasteText'));
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
        <TabsTrigger value="url">{t('jobs.create.tabUrl')}</TabsTrigger>
        <TabsTrigger value="text">{t('jobs.create.tabText')}</TabsTrigger>
      </TabsList>

      <TabsContent value="url" className="mt-4">
        <form onSubmit={submitUrl} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="job-url">{t('jobs.create.urlLabel')}</Label>
            <Input
              id="job-url"
              type="url"
              placeholder={t('jobs.create.urlPlaceholder')}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={fromUrl.isPending}>
              {fromUrl.isPending ? t('jobs.create.adding') : t('jobs.create.add')}
            </Button>
          </div>
        </form>
      </TabsContent>

      <TabsContent value="text" className="mt-4">
        <form onSubmit={submitText} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="job-text">{t('jobs.create.textLabel')}</Label>
            <Textarea
              id="job-text"
              rows={10}
              placeholder={t('jobs.create.textPlaceholder')}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="job-source-url">{t('jobs.create.sourceUrlLabel')}</Label>
            <Input
              id="job-source-url"
              type="url"
              placeholder={t('jobs.create.urlPlaceholder')}
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={fromText.isPending}>
              {fromText.isPending ? t('jobs.create.adding') : t('jobs.create.add')}
            </Button>
          </div>
        </form>
      </TabsContent>
    </Tabs>
  );
}
