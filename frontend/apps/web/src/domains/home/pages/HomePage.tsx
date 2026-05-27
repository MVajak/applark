import { useMemo } from 'react';
import { ArrowRight, Briefcase, CheckCircle2, Command, FileText, Loader2, OctagonX, Plus } from 'lucide-react';
import { motion } from 'motion/react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '@applark/ui';

import { useGetJobs } from '@/domains/api/generated/jobs/jobs';
import { JobStatus } from '@/domains/api/generated/model/jobStatus';
import { QuickActionCard } from '@/domains/home/components/QuickActionCard';
import { RecentJobsStrip } from '@/domains/home/components/RecentJobsStrip';
import { StatCard } from '@/domains/home/components/StatCard';
import { ACTIVE_STATUSES } from '@/domains/jobs/constants';
import { EmptyState } from '@/domains/shell/components/EmptyState';
import { useSpotlightStore } from '@/domains/shell/spotlight-store';

export function HomePage() {
  const { data, isLoading } = useGetJobs();
  const navigate = useNavigate();
  const openSpotlight = useSpotlightStore((s) => s.open);

  const stats = useMemo(() => {
    const jobs = data ?? [];
    return {
      total: jobs.length,
      ready: jobs.filter((j) => j.status === JobStatus.ready).length,
      active: jobs.filter((j) => ACTIVE_STATUSES.has(j.status)).length,
      failed: jobs.filter((j) => j.status === JobStatus.failed).length,
    };
  }, [data]);

  const recent = useMemo(() => (data ?? []).slice(0, 3), [data]);
  const hasJobs = (data?.length ?? 0) > 0;

  return (
    <div className="space-y-12">
      <Hero />

      <Section delay={0.05}>
        <SectionHeader title="Overview" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard icon={Briefcase} label="Total jobs" value={stats.total} loading={isLoading} />
          <StatCard icon={CheckCircle2} label="Ready" value={stats.ready} tone="positive" loading={isLoading} />
          <StatCard icon={Loader2} label="In progress" value={stats.active} tone="warning" loading={isLoading} />
          <StatCard icon={OctagonX} label="Failed" value={stats.failed} tone="destructive" loading={isLoading} />
        </div>
      </Section>

      <Section delay={0.1}>
        <SectionHeader
          title="Recent jobs"
          action={
            hasJobs ? (
              <Button variant="ghost" size="sm" asChild>
                <Link to="/jobs">
                  See all <ArrowRight className="size-3.5" />
                </Link>
              </Button>
            ) : undefined
          }
        />
        {hasJobs ? (
          <RecentJobsStrip jobs={recent} />
        ) : (
          <EmptyState
            icon={Briefcase}
            title="No jobs yet"
            description="Add your first job posting to see Applark match it against your CV."
            action={
              <Button variant="gradient" onClick={() => navigate('/jobs?new=url')}>
                <Plus className="size-4" /> Add your first job
              </Button>
            }
          />
        )}
      </Section>

      <Section delay={0.15}>
        <SectionHeader title="Quick actions" />
        <div className="grid gap-3 sm:grid-cols-3">
          <QuickActionCard
            icon={Plus}
            label="Add a job"
            description="Paste a posting URL or text — Applark scrapes and extracts."
            onClick={() => navigate('/jobs?new=url')}
          />
          <QuickActionCard
            icon={FileText}
            label="Upload a CV"
            description="Drop a PDF — Applark parses it for matching against any job."
            onClick={() => navigate('/cv')}
          />
          <QuickActionCard
            icon={Command}
            label="Command palette"
            description="Press ⌘K anywhere to jump to any page or run a quick action."
            onClick={() => openSpotlight()}
          />
        </div>
      </Section>
    </div>
  );
}

function Hero() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="relative -mx-6 overflow-hidden rounded-3xl border border-border/60 px-6 py-14 sm:px-12 sm:py-16"
    >
      <div className="absolute inset-0 bg-glass-mesh opacity-50" aria-hidden />
      <div className="relative space-y-6">
        <div className="space-y-3">
          <h1 className="text-display-default-bold text-gradient tracking-tight md:text-display-large-bold">
            Applark
          </h1>
          <p className="max-w-xl text-body-large text-muted-foreground">
            Land the role. Tailor your story to every job posting — match, draft, and prep with your CV as the anchor.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button variant="gradient" size="lg" asChild>
            <Link to="/jobs">
              <Briefcase className="size-4" /> Browse jobs <ArrowRight className="size-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link to="/cv">
              <FileText className="size-4" /> Manage CVs
            </Link>
          </Button>
        </div>
      </div>
    </motion.section>
  );
}

function Section({ delay, children }: { delay: number; children: React.ReactNode }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: 'easeOut' }}
      className="space-y-4"
    >
      {children}
    </motion.section>
  );
}

function SectionHeader({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <header className="flex items-center justify-between">
      <h2 className="text-title-small-bold">{title}</h2>
      {action}
    </header>
  );
}
