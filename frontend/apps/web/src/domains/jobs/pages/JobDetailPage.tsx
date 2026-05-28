import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, ArrowLeft, RotateCcw } from 'lucide-react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { useTranslation } from '@applark/i18n';
import { Alert, AlertDescription, AlertTitle, Button, Skeleton } from '@applark/ui';

import { useGetJob, useRetryJob } from '@/domains/api/generated/jobs/jobs';
import { JobStatus } from '@/domains/api/generated/model/jobStatus';
import { isJobActionId, type JobActionId } from '@/domains/jobs/actions';
import { ActionGrid } from '@/domains/jobs/components/ActionGrid';
import { FeatureDrawer } from '@/domains/jobs/components/FeatureDrawer';
import { JobDetailHeader } from '@/domains/jobs/components/JobDetailHeader';
import { JobStatusTimeline } from '@/domains/jobs/components/JobStatusTimeline';
import { RequirementsList } from '@/domains/jobs/components/RequirementsList';
import { ACTIVE_STATUSES } from '@/domains/jobs/constants';

export function JobDetailPage() {
  const { t } = useTranslation();
  const { id = '' } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const jobQuery = useGetJob(id, {
    query: {
      enabled: !!id,
    },
  });

  const retry = useRetryJob({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: jobQuery.queryKey });
        toast.success(t('jobs.detail.toastRetrying'));
      },
      onError: () => toast.error(t('jobs.detail.toastRetryFailed')),
    },
  });

  const actionParam = searchParams.get('action');
  const activeAction: JobActionId | null = isJobActionId(actionParam) ? actionParam : null;

  const openAction = useCallback(
    (action: JobActionId) => {
      const next = new URLSearchParams(searchParams);
      next.set('action', action);
      setSearchParams(next);
    },
    [searchParams, setSearchParams]
  );

  const closeAction = useCallback(() => {
    const next = new URLSearchParams(searchParams);
    next.delete('action');
    setSearchParams(next);
  }, [searchParams, setSearchParams]);

  if (jobQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (!jobQuery.data) {
    return (
      <div className="space-y-4">
        <BackLink />
        <p className="text-body-default text-muted-foreground">{t('jobs.detail.notFound')}</p>
      </div>
    );
  }

  const job = jobQuery.data;

  return (
    <div className="space-y-8">
      <BackLink />

      <JobDetailHeader job={job} />

      <JobStatusTimeline status={job.status} />

      {job.status === JobStatus.failed && job.error_message && (
        <Alert variant="destructive">
          <AlertTriangle className="size-4" />
          <AlertTitle>{t('jobs.detail.failedTitle')}</AlertTitle>
          <AlertDescription className="space-y-2">
            <p className="whitespace-pre-wrap font-mono text-body-small">{job.error_message}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => retry.mutate({ jobId: job.id })}
              disabled={retry.isPending}
            >
              <RotateCcw className="size-3" /> {retry.isPending ? t('jobs.detail.retrying') : t('jobs.detail.retry')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {ACTIVE_STATUSES.has(job.status) && (
        <Alert>
          <AlertTitle className="animate-pulse">{t('jobs.detail.processingTitle')}</AlertTitle>
          <AlertDescription>{t('jobs.detail.processing', { status: job.status })}</AlertDescription>
        </Alert>
      )}

      <section className="space-y-3">
        <h2 className="text-title-small-bold">{t('jobs.detail.requirements')}</h2>
        <RequirementsList requirements={job.requirements} />
      </section>

      {job.status === JobStatus.ready && (
        <section className="space-y-3">
          <h2 className="text-title-small-bold">{t('jobs.detail.nextSteps')}</h2>
          <ActionGrid onSelect={openAction} />
        </section>
      )}

      <FeatureDrawer
        action={activeAction}
        jobId={job.id}
        open={activeAction !== null}
        onOpenChange={(open) => {
          if (!open) closeAction();
        }}
      />
    </div>
  );
}

function BackLink() {
  const { t } = useTranslation();
  return (
    <Link
      to="/jobs"
      className="inline-flex items-center gap-1.5 text-body-default text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft className="size-4" /> {t('nav.jobs')}
    </Link>
  );
}
