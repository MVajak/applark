import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { Controller, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';

import { i18n, useTranslation } from '@applark/i18n';
import {
  Button,
  Field,
  FieldError,
  FieldLabel,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Textarea,
} from '@applark/ui';

import { getErrorDetail, getErrorDetailObject, getErrorStatus } from '@/domains/api/client';
import { getGetJobsQueryKey, useCreateJobFromText, useCreateJobFromUrl } from '@/domains/api/generated/jobs/jobs';
import { IntakePaywall } from '@/domains/billing/components/IntakePaywall';
import { useSubscription } from '@/domains/billing/hooks/useSubscription';

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

/** AI job import is a paid capability — free users get the paywall instead. */
export function JobCreateForm({ onCreated }: { onCreated: () => void }) {
  const { isSubscribed, isLoading } = useSubscription();
  if (isLoading) return null;
  if (!isSubscribed) return <IntakePaywall />;
  return <JobCreateFormFields onCreated={onCreated} />;
}

function JobCreateFormFields({ onCreated }: { onCreated: () => void }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const invalidateJobs = () => queryClient.invalidateQueries({ queryKey: getGetJobsQueryKey() });

  const urlSchema = z.object({
    url: z.url({ message: t('jobs.create.errorPasteUrl') }),
  });
  type UrlValues = z.infer<typeof urlSchema>;
  const urlForm = useForm<UrlValues>({
    resolver: zodResolver(urlSchema),
    defaultValues: { url: '' },
  });

  const textSchema = z.object({
    rawText: z.string().trim().min(1, t('jobs.create.errorPasteText')),
    // Optional URL: blank is allowed; if non-blank it must be a valid URL.
    sourceUrl: z.union([z.literal(''), z.url({ message: t('jobs.create.errorInvalidUrl') })]),
  });
  type TextValues = z.infer<typeof textSchema>;
  const textForm = useForm<TextValues>({
    resolver: zodResolver(textSchema),
    defaultValues: { rawText: '', sourceUrl: '' },
  });

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

  return (
    <Tabs defaultValue="url" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="url">{t('jobs.create.tabUrl')}</TabsTrigger>
        <TabsTrigger value="text">{t('jobs.create.tabText')}</TabsTrigger>
      </TabsList>

      <TabsContent value="url" className="mt-4">
        <form
          onSubmit={urlForm.handleSubmit(({ url }) => fromUrl.mutate({ data: { source_url: url.trim() } }))}
          className="space-y-4"
          noValidate
        >
          <Controller
            name="url"
            control={urlForm.control}
            render={({ field }) => (
              <Field data-invalid={!!urlForm.formState.errors.url}>
                <FieldLabel htmlFor="job-url">{t('jobs.create.urlLabel')}</FieldLabel>
                <Input
                  id="job-url"
                  type="url"
                  placeholder={t('jobs.create.urlPlaceholder')}
                  aria-invalid={!!urlForm.formState.errors.url}
                  {...field}
                />
                {urlForm.formState.errors.url && <FieldError>{urlForm.formState.errors.url.message}</FieldError>}
              </Field>
            )}
          />
          <div className="flex justify-end">
            <Button type="submit" disabled={fromUrl.isPending}>
              {fromUrl.isPending ? t('jobs.create.adding') : t('jobs.create.add')}
            </Button>
          </div>
        </form>
      </TabsContent>

      <TabsContent value="text" className="mt-4">
        <form
          onSubmit={textForm.handleSubmit(({ rawText, sourceUrl }) => {
            const trimmedSource = sourceUrl.trim();
            fromText.mutate({
              data: { raw_text: rawText, source_url: trimmedSource === '' ? null : trimmedSource },
            });
          })}
          className="space-y-4"
          noValidate
        >
          <Controller
            name="rawText"
            control={textForm.control}
            render={({ field }) => (
              <Field data-invalid={!!textForm.formState.errors.rawText}>
                <FieldLabel htmlFor="job-text">{t('jobs.create.textLabel')}</FieldLabel>
                <Textarea
                  id="job-text"
                  rows={10}
                  placeholder={t('jobs.create.textPlaceholder')}
                  aria-invalid={!!textForm.formState.errors.rawText}
                  {...field}
                />
                {textForm.formState.errors.rawText && (
                  <FieldError>{textForm.formState.errors.rawText.message}</FieldError>
                )}
              </Field>
            )}
          />
          <Controller
            name="sourceUrl"
            control={textForm.control}
            render={({ field }) => (
              <Field data-invalid={!!textForm.formState.errors.sourceUrl}>
                <FieldLabel htmlFor="job-source-url">{t('jobs.create.sourceUrlLabel')}</FieldLabel>
                <Input
                  id="job-source-url"
                  type="url"
                  placeholder={t('jobs.create.urlPlaceholder')}
                  aria-invalid={!!textForm.formState.errors.sourceUrl}
                  {...field}
                />
                {textForm.formState.errors.sourceUrl && (
                  <FieldError>{textForm.formState.errors.sourceUrl.message}</FieldError>
                )}
              </Field>
            )}
          />
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
